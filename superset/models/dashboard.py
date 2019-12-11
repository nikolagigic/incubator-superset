# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import json
import logging
from copy import copy
from typing import Set, Optional, List, Dict, Any, Type
from urllib import parse

from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders
from markupsafe import Markup, escape
import sqlalchemy as sqla
from sqlalchemy import Column, Integer, String, Text, Boolean, MetaData, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, subqueryload, make_transient

from superset import security_manager, db, ConnectorRegistry
from superset.legacy import update_time_range
from superset.models.helpers import AuditMixinNullable, ImportMixin
from superset.utils import core as utils
from superset.viz import BaseViz, viz_types


def set_related_perm(mapper, connection, target):
    src_class = target.cls_model
    id_ = target.datasource_id
    if id_:
        ds = db.session.query(src_class).filter_by(id=int(id_)).first()
        if ds:
            target.perm = ds.perm
            target.schema_perm = ds.schema_perm


metadata = Model.metadata  # pylint: disable=no-member
dashboard_slices = Table(
    "dashboard_slices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("dashboard_id", Integer, ForeignKey("dashboards.id")),
    Column("slice_id", Integer, ForeignKey("slices.id")),
    UniqueConstraint("dashboard_id", "slice_id"),
)


dashboard_user = Table(
    "dashboard_user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("ab_user.id")),
    Column("dashboard_id", Integer, ForeignKey("dashboards.id")),
)


slice_user = Table(
    "slice_user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("ab_user.id")),
    Column("slice_id", Integer, ForeignKey("slices.id")),
)


class Slice(
    Model, AuditMixinNullable, ImportMixin
):  # pylint: disable=too-many-public-methods

    """A slice is essentially a report or a view on data"""

    __tablename__ = "slices"
    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    slice_name = Column(String(250))
    datasource_id = Column(Integer)
    datasource_type = Column(String(200))
    datasource_name = Column(String(2000))
    viz_type = Column(String(250))
    params = Column(Text)
    description = Column(Text)
    cache_timeout = Column(Integer)
    perm = Column(String(1000))
    schema_perm = Column(String(1000))
    owners = relationship(security_manager.user_model, secondary=slice_user)
    token = ""

    export_fields = [
        "slice_name",
        "datasource_type",
        "datasource_name",
        "viz_type",
        "params",
        "cache_timeout",
    ]

    def __repr__(self):
        return self.slice_name or str(self.id)

    @property
    def cls_model(self) -> Type["BaseDatasource"]:
        return ConnectorRegistry.sources[self.datasource_type]

    @property
    def datasource(self) -> "BaseDatasource":
        return self.get_datasource

    def clone(self) -> "Slice":
        return Slice(
            slice_name=self.slice_name,
            datasource_id=self.datasource_id,
            datasource_type=self.datasource_type,
            datasource_name=self.datasource_name,
            viz_type=self.viz_type,
            params=self.params,
            description=self.description,
            cache_timeout=self.cache_timeout,
        )

    # pylint: disable=using-constant-test
    @datasource.getter  # type: ignore
    @utils.memoized
    def get_datasource(self) -> Optional["BaseDatasource"]:
        return db.session.query(self.cls_model).filter_by(id=self.datasource_id).first()

    @renders("datasource_name")
    def datasource_link(self) -> Optional[Markup]:
        # pylint: disable=no-member
        datasource = self.datasource
        return datasource.link if datasource else None

    def datasource_name_text(self) -> Optional[str]:
        # pylint: disable=no-member
        datasource = self.datasource
        return datasource.name if datasource else None

    @property
    def datasource_edit_url(self) -> Optional[str]:
        # pylint: disable=no-member
        datasource = self.datasource
        return datasource.url if datasource else None

    # pylint: enable=using-constant-test

    @property  # type: ignore
    @utils.memoized
    def viz(self) -> BaseViz:
        d = json.loads(self.params)
        viz_class = viz_types[self.viz_type]
        return viz_class(datasource=self.datasource, form_data=d)

    @property
    def description_markeddown(self) -> str:
        return utils.markdown(self.description)

    @property
    def data(self) -> Dict[str, Any]:
        """Data used to render slice in templates"""
        d: Dict[str, Any] = {}
        self.token = ""
        try:
            d = self.viz.data
            self.token = d.get("token")  # type: ignore
        except Exception as e:  # pylint: disable=broad-except
            logging.exception(e)
            d["error"] = str(e)
        return {
            "datasource": self.datasource_name,
            "description": self.description,
            "description_markeddown": self.description_markeddown,
            "edit_url": self.edit_url,
            "form_data": self.form_data,
            "slice_id": self.id,
            "slice_name": self.slice_name,
            "slice_url": self.slice_url,
            "modified": self.modified(),
            "changed_on_humanized": self.changed_on_humanized,
            "changed_on": self.changed_on.isoformat(),
        }

    @property
    def json_data(self) -> str:
        return json.dumps(self.data)

    @property
    def form_data(self) -> Dict[str, Any]:
        form_data: Dict[str, Any] = {}
        try:
            form_data = json.loads(self.params)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Malformed json in slice's params")
            logging.exception(e)
        form_data.update(
            {
                "slice_id": self.id,
                "viz_type": self.viz_type,
                "datasource": "{}__{}".format(self.datasource_id, self.datasource_type),
            }
        )

        if self.cache_timeout:
            form_data["cache_timeout"] = self.cache_timeout
        update_time_range(form_data)
        return form_data

    def get_explore_url(
        self,
        base_url: str = "/superset/explore",
        overrides: Optional[Dict[str, Any]] = None,
    ) -> str:
        overrides = overrides or {}
        form_data = {"slice_id": self.id}
        form_data.update(overrides)
        params = parse.quote(json.dumps(form_data))
        return f"{base_url}/?form_data={params}"

    @property
    def slice_url(self) -> str:
        """Defines the url to access the slice"""
        return self.get_explore_url()

    @property
    def explore_json_url(self) -> str:
        """Defines the url to access the slice"""
        return self.get_explore_url("/superset/explore_json")

    @property
    def edit_url(self) -> str:
        return f"/chart/edit/{self.id}"

    @property
    def chart(self) -> str:
        return self.slice_name or "<empty>"

    @property
    def slice_link(self) -> Markup:
        name = escape(self.chart)
        return Markup(f'<a href="{self.url}">{name}</a>')

    def get_viz(self, force: bool = False) -> BaseViz:
        """Creates :py:class:viz.BaseViz object from the url_params_multidict.

        :return: object of the 'viz_type' type that is taken from the
            url_params_multidict or self.params.
        :rtype: :py:class:viz.BaseViz
        """
        slice_params = json.loads(self.params)
        slice_params["slice_id"] = self.id
        slice_params["json"] = "false"
        slice_params["slice_name"] = self.slice_name
        slice_params["viz_type"] = self.viz_type if self.viz_type else "table"

        return viz_types[slice_params.get("viz_type")](
            self.datasource, form_data=slice_params, force=force
        )

    @property
    def icons(self) -> str:
        return f"""
        <a
                href="{self.datasource_edit_url}"
                data-toggle="tooltip"
                title="{self.datasource}">
            <i class="fa fa-database"></i>
        </a>
        """

    @classmethod
    def import_obj(
        cls,
        slc_to_import: "Slice",
        slc_to_override: Optional["Slice"],
        import_time: Optional[int] = None,
    ) -> int:
        """Inserts or overrides slc in the database.

        remote_id and import_time fields in params_dict are set to track the
        slice origin and ensure correct overrides for multiple imports.
        Slice.perm is used to find the datasources and connect them.

        :param Slice slc_to_import: Slice object to import
        :param Slice slc_to_override: Slice to replace, id matches remote_id
        :returns: The resulting id for the imported slice
        :rtype: int
        """
        session = db.session
        make_transient(slc_to_import)
        slc_to_import.dashboards = []
        slc_to_import.alter_params(remote_id=slc_to_import.id, import_time=import_time)

        slc_to_import = slc_to_import.copy()
        slc_to_import.reset_ownership()
        params = slc_to_import.params_dict
        slc_to_import.datasource_id = ConnectorRegistry.get_datasource_by_name(  # type: ignore
            session,
            slc_to_import.datasource_type,
            params["datasource_name"],
            params["schema"],
            params["database_name"],
        ).id
        if slc_to_override:
            slc_to_override.override(slc_to_import)
            session.flush()
            return slc_to_override.id
        session.add(slc_to_import)
        logging.info("Final slice: %s", str(slc_to_import.to_json()))
        session.flush()
        return slc_to_import.id

    @property
    def url(self) -> str:
        return f"/superset/explore/?form_data=%7B%22slice_id%22%3A%20{self.id}%7D"

sqla.event.listen(Slice, "before_insert", set_related_perm)
sqla.event.listen(Slice, "before_update", set_related_perm)


class Dashboard(  # pylint: disable=too-many-instance-attributes
    Model, AuditMixinNullable, ImportMixin
):

    """The dashboard object!"""

    __tablename__ = "dashboards"
    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    dashboard_title = Column(String(500))
    position_json = Column(utils.MediumText())
    description = Column(Text)
    css = Column(Text)
    json_metadata = Column(Text)
    slug = Column(String(255), unique=True)
    slices = relationship("Slice", secondary=dashboard_slices, backref="dashboards")
    owners = relationship(security_manager.user_model, secondary=dashboard_user)
    published = Column(Boolean, default=False)

    export_fields = [
        "dashboard_title",
        "position_json",
        "json_metadata",
        "description",
        "css",
        "slug",
    ]

    def __repr__(self):
        return self.dashboard_title or str(self.id)

    @property
    def table_names(self) -> str:
        # pylint: disable=no-member
        return ", ".join(str(s.datasource.full_name) for s in self.slices)

    @property
    def url(self) -> str:
        if self.json_metadata:
            # add default_filters to the preselect_filters of dashboard
            json_metadata = json.loads(self.json_metadata)
            default_filters = json_metadata.get("default_filters")
            # make sure default_filters is not empty and is valid
            if default_filters and default_filters != "{}":
                try:
                    if json.loads(default_filters):
                        filters = parse.quote(default_filters.encode("utf8"))
                        return "/superset/dashboard/{}/?preselect_filters={}".format(
                            self.slug or self.id, filters
                        )
                except Exception:  # pylint: disable=broad-except
                    pass
        return f"/superset/dashboard/{self.slug or self.id}/"

    @property
    def datasources(self) -> Set[Optional["BaseDatasource"]]:
        return {slc.datasource for slc in self.slices}

    @property
    def charts(self) -> List[Optional["BaseDatasource"]]:
        return [slc.chart for slc in self.slices]

    @property
    def sqla_metadata(self) -> None:
        # pylint: disable=no-member
        meta = MetaData(bind=self.get_sqla_engine())
        meta.reflect()

    def dashboard_link(self) -> Markup:
        title = escape(self.dashboard_title or "<empty>")
        return Markup(f'<a href="{self.url}">{title}</a>')

    @property
    def data(self) -> Dict[str, Any]:
        positions = self.position_json
        if positions:
            positions = json.loads(positions)
        return {
            "id": self.id,
            "metadata": self.params_dict,
            "css": self.css,
            "dashboard_title": self.dashboard_title,
            "published": self.published,
            "slug": self.slug,
            "slices": [slc.data for slc in self.slices],
            "position_json": positions,
        }

    @property
    def params(self) -> str:
        return self.json_metadata

    @params.setter
    def params(self, value: str) -> None:
        self.json_metadata = value

    @property
    def position(self) -> Dict:
        if self.position_json:
            return json.loads(self.position_json)
        return {}

    @classmethod
    def import_obj(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        cls, dashboard_to_import: "Dashboard", import_time: Optional[int] = None
    ) -> int:
        """Imports the dashboard from the object to the database.

         Once dashboard is imported, json_metadata field is extended and stores
         remote_id and import_time. It helps to decide if the dashboard has to
         be overridden or just copies over. Slices that belong to this
         dashboard will be wired to existing tables. This function can be used
         to import/export dashboards between multiple superset instances.
         Audit metadata isn't copied over.
        """

        def alter_positions(dashboard, old_to_new_slc_id_dict):
            """ Updates slice_ids in the position json.

            Sample position_json data:
            {
                "DASHBOARD_VERSION_KEY": "v2",
                "DASHBOARD_ROOT_ID": {
                    "type": "DASHBOARD_ROOT_TYPE",
                    "id": "DASHBOARD_ROOT_ID",
                    "children": ["DASHBOARD_GRID_ID"]
                },
                "DASHBOARD_GRID_ID": {
                    "type": "DASHBOARD_GRID_TYPE",
                    "id": "DASHBOARD_GRID_ID",
                    "children": ["DASHBOARD_CHART_TYPE-2"]
                },
                "DASHBOARD_CHART_TYPE-2": {
                    "type": "DASHBOARD_CHART_TYPE",
                    "id": "DASHBOARD_CHART_TYPE-2",
                    "children": [],
                    "meta": {
                        "width": 4,
                        "height": 50,
                        "chartId": 118
                    }
                },
            }
            """
            position_data = json.loads(dashboard.position_json)
            position_json = position_data.values()
            for value in position_json:
                if (
                    isinstance(value, dict)
                    and value.get("meta")
                    and value.get("meta").get("chartId")
                ):
                    old_slice_id = value.get("meta").get("chartId")

                    if old_slice_id in old_to_new_slc_id_dict:
                        value["meta"]["chartId"] = old_to_new_slc_id_dict[old_slice_id]
            dashboard.position_json = json.dumps(position_data)

        logging.info(
            "Started import of the dashboard: %s", dashboard_to_import.to_json()
        )
        session = db.session
        logging.info("Dashboard has %d slices", len(dashboard_to_import.slices))
        # copy slices object as Slice.import_slice will mutate the slice
        # and will remove the existing dashboard - slice association
        slices = copy(dashboard_to_import.slices)
        old_to_new_slc_id_dict = {}
        new_filter_immune_slices = []
        new_filter_immune_slice_fields = {}
        new_timed_refresh_immune_slices = []
        new_expanded_slices = {}
        i_params_dict = dashboard_to_import.params_dict
        remote_id_slice_map = {
            slc.params_dict["remote_id"]: slc
            for slc in session.query(Slice).all()
            if "remote_id" in slc.params_dict
        }
        for slc in slices:
            logging.info(
                "Importing slice %s from the dashboard: %s",
                slc.to_json(),
                dashboard_to_import.dashboard_title,
            )
            remote_slc = remote_id_slice_map.get(slc.id)
            new_slc_id = Slice.import_obj(slc, remote_slc, import_time=import_time)
            old_to_new_slc_id_dict[slc.id] = new_slc_id
            # update json metadata that deals with slice ids
            new_slc_id_str = "{}".format(new_slc_id)
            old_slc_id_str = "{}".format(slc.id)
            if (
                "filter_immune_slices" in i_params_dict
                and old_slc_id_str in i_params_dict["filter_immune_slices"]
            ):
                new_filter_immune_slices.append(new_slc_id_str)
            if (
                "filter_immune_slice_fields" in i_params_dict
                and old_slc_id_str in i_params_dict["filter_immune_slice_fields"]
            ):
                new_filter_immune_slice_fields[new_slc_id_str] = i_params_dict[
                    "filter_immune_slice_fields"
                ][old_slc_id_str]
            if (
                "timed_refresh_immune_slices" in i_params_dict
                and old_slc_id_str in i_params_dict["timed_refresh_immune_slices"]
            ):
                new_timed_refresh_immune_slices.append(new_slc_id_str)
            if (
                "expanded_slices" in i_params_dict
                and old_slc_id_str in i_params_dict["expanded_slices"]
            ):
                new_expanded_slices[new_slc_id_str] = i_params_dict["expanded_slices"][
                    old_slc_id_str
                ]

        # override the dashboard
        existing_dashboard = None
        for dash in session.query(Dashboard).all():
            if (
                "remote_id" in dash.params_dict
                and dash.params_dict["remote_id"] == dashboard_to_import.id
            ):
                existing_dashboard = dash

        dashboard_to_import = dashboard_to_import.copy()
        dashboard_to_import.id = None
        dashboard_to_import.reset_ownership()
        # position_json can be empty for dashboards
        # with charts added from chart-edit page and without re-arranging
        if dashboard_to_import.position_json:
            alter_positions(dashboard_to_import, old_to_new_slc_id_dict)
        dashboard_to_import.alter_params(import_time=import_time)
        if new_expanded_slices:
            dashboard_to_import.alter_params(expanded_slices=new_expanded_slices)
        if new_filter_immune_slices:
            dashboard_to_import.alter_params(
                filter_immune_slices=new_filter_immune_slices
            )
        if new_filter_immune_slice_fields:
            dashboard_to_import.alter_params(
                filter_immune_slice_fields=new_filter_immune_slice_fields
            )
        if new_timed_refresh_immune_slices:
            dashboard_to_import.alter_params(
                timed_refresh_immune_slices=new_timed_refresh_immune_slices
            )

        new_slices = (
            session.query(Slice)
            .filter(Slice.id.in_(old_to_new_slc_id_dict.values()))
            .all()
        )

        if existing_dashboard:
            existing_dashboard.override(dashboard_to_import)
            existing_dashboard.slices = new_slices
            session.flush()
            return existing_dashboard.id

        dashboard_to_import.slices = new_slices
        session.add(dashboard_to_import)
        session.flush()
        return dashboard_to_import.id  # type: ignore

    @classmethod
    def export_dashboards(  # pylint: disable=too-many-locals
        cls, dashboard_ids: List
    ) -> str:
        copied_dashboards = []
        datasource_ids = set()
        for dashboard_id in dashboard_ids:
            # make sure that dashboard_id is an integer
            dashboard_id = int(dashboard_id)
            dashboard = (
                db.session.query(Dashboard)
                .options(subqueryload(Dashboard.slices))
                .filter_by(id=dashboard_id)
                .first()
            )
            # remove ids and relations (like owners, created by, slices, ...)
            copied_dashboard = dashboard.copy()
            for slc in dashboard.slices:
                datasource_ids.add((slc.datasource_id, slc.datasource_type))
                copied_slc = slc.copy()
                # save original id into json
                # we need it to update dashboard's json metadata on import
                copied_slc.id = slc.id
                # add extra params for the import
                copied_slc.alter_params(
                    remote_id=slc.id,
                    datasource_name=slc.datasource.datasource_name,
                    schema=slc.datasource.schema,
                    database_name=slc.datasource.database.name,
                )
                # set slices without creating ORM relations
                slices = copied_dashboard.__dict__.setdefault("slices", [])
                slices.append(copied_slc)
            copied_dashboard.alter_params(remote_id=dashboard_id)
            copied_dashboards.append(copied_dashboard)

        eager_datasources = []
        for datasource_id, datasource_type in datasource_ids:
            eager_datasource = ConnectorRegistry.get_eager_datasource(
                db.session, datasource_type, datasource_id
            )
            copied_datasource = eager_datasource.copy()
            copied_datasource.alter_params(
                remote_id=eager_datasource.id,
                database_name=eager_datasource.database.name,
            )
            datasource_class = copied_datasource.__class__
            for field_name in datasource_class.export_children:
                field_val = getattr(eager_datasource, field_name).copy()
                # set children without creating ORM relations
                copied_datasource.__dict__[field_name] = field_val
            eager_datasources.append(copied_datasource)

        return json.dumps(
            {"dashboards": copied_dashboards, "datasources": eager_datasources},
            cls=utils.DashboardEncoder,
            indent=4,
        )
