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

from typing import Dict, Iterable, List, Tuple

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()

PvmType = Tuple[str, str]
PvmMigrationMapType = Dict[PvmType, Tuple[PvmType, ...]]

# Partial freeze of the current metadata db schema


class Permission(Base):  # type: ignore
    __tablename__ = "ab_permission"
    id = Column(Integer, Sequence("ab_permission_id_seq"), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"{self.name}"


class ViewMenu(Base):  # type: ignore
    __tablename__ = "ab_view_menu"
    id = Column(Integer, Sequence("ab_view_menu_id_seq"), primary_key=True)
    name = Column(String(250), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"{self.name}"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, self.__class__)) and (self.name == other.name)

    def __neq__(self, other: object) -> bool:
        return (isinstance(other, self.__class__)) and self.name != other.name


assoc_permissionview_role = Table(
    "ab_permission_view_role",
    Base.metadata,
    Column("id", Integer, Sequence("ab_permission_view_role_id_seq"), primary_key=True),
    Column("permission_view_id", Integer, ForeignKey("ab_permission_view.id")),
    Column("role_id", Integer, ForeignKey("ab_role.id")),
    UniqueConstraint("permission_view_id", "role_id"),
)


class Role(Base):  # type: ignore
    __tablename__ = "ab_role"

    id = Column(Integer, Sequence("ab_role_id_seq"), primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    permissions = relationship(
        "PermissionView", secondary=assoc_permissionview_role, backref="role"
    )

    def __repr__(self) -> str:
        return f"{self.name}"


class PermissionView(Base):  # type: ignore
    __tablename__ = "ab_permission_view"
    __table_args__ = (UniqueConstraint("permission_id", "view_menu_id"),)
    id = Column(Integer, Sequence("ab_permission_view_id_seq"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("ab_permission.id"))
    permission = relationship("Permission")
    view_menu_id = Column(Integer, ForeignKey("ab_view_menu.id"))
    view_menu = relationship("ViewMenu")

    def __repr__(self) -> str:
        return f"{self.permission} {self.view_menu}"


def add_pvms(
    session: Session, pvm_data: Dict[str, Tuple[str, ...]], commit: bool = False
) -> None:
    for view_name, permissions in pvm_data.items():
        # Check and add the new View
        new_view = (
            session.query(ViewMenu).filter(ViewMenu.name == view_name).one_or_none()
        )
        if not new_view:
            new_view = ViewMenu(name=view_name)
            session.add(new_view)
        for permission_name in permissions:
            # Check and add the new Permission
            new_permission = (
                session.query(Permission)
                .filter(Permission.name == permission_name)
                .one_or_none()
            )
            if not new_permission:
                new_permission = Permission(name=permission_name)
                session.add(new_permission)
            # Check and add the new PVM
            new_pvm = (
                session.query(PermissionView)
                .filter(
                    PermissionView.view_menu_id == new_view.id,
                    PermissionView.permission_id == new_permission.id,
                )
                .one_or_none()
            )
            if not new_pvm:
                new_pvm = PermissionView(view_menu=new_view, permission=new_permission)
                session.add(new_pvm)
    if commit:
        session.commit()


def find_pvm(session: Session, view_name: str, permission_name: str) -> PermissionView:
    return (
        session.query(PermissionView)
        .join(Permission)
        .join(ViewMenu)
        .filter(ViewMenu.name == view_name, Permission.name == permission_name)
    ).one_or_none()


def migrate_roles(
    session: Session, pvm_key_map: PvmMigrationMapType, commit: bool = False,
) -> None:
    from sqlalchemy.orm import Load

    pvm_map: Dict[PermissionView, List[PermissionView]] = {}
    for old_pvm_key, new_pvms_ in pvm_key_map.items():
        old_pvm = find_pvm(session, old_pvm_key[0], old_pvm_key[1])
        if old_pvm:
            for new_pvm_key in new_pvms_:
                new_pvm = find_pvm(session, new_pvm_key[0], new_pvm_key[1])
                if old_pvm not in pvm_map:
                    pvm_map[old_pvm] = [new_pvm]
                else:
                    pvm_map[old_pvm].append(new_pvm)

    # Replace old permissions by the new ones on all existing roles
    roles = session.query(Role).options(Load(Role).joinedload(Role.permissions)).all()
    for role in roles:
        for old_pvm, new_pvms in pvm_map.items():
            if old_pvm in role.permissions:
                print(f"Removing {old_pvm} from {role}")
                role.permissions.remove(old_pvm)
                for new_pvm in new_pvms:
                    if new_pvm not in role.permissions:
                        print(f"Add {new_pvm} to {role}")
                        role.permissions.append(new_pvm)
        session.merge(role)

    # Delete old permissions
    for old_pvm, new_pvms in pvm_map.items():
        old_permission_name = old_pvm.permission.name
        old_view_name = old_pvm.view_menu.name
        print(f"Going to delete pvm: {old_pvm}")
        session.delete(old_pvm)
        pvms_with_permission = (
            session.query(PermissionView)
            .join(Permission)
            .filter(Permission.name == old_permission_name)
        ).first()
        if not pvms_with_permission:
            print(f"Going to delete permission: {old_pvm.permission}")
            session.delete(old_pvm.permission)
        pvms_with_view_menu = (
            session.query(PermissionView)
            .join(ViewMenu)
            .filter(ViewMenu.name == old_view_name)
        ).first()
        if not pvms_with_view_menu:
            print(f"Going to delete view_menu: {old_pvm.view_menu}")
            session.delete(old_pvm.view_menu)

    if commit:
        session.commit()


def get_reversed_new_pvms(pvm_map: PvmMigrationMapType) -> Dict[str, Tuple[str, ...]]:
    reversed_pvms: Dict[str, Tuple[str, ...]] = {}
    for old_pvm, new_pvms in pvm_map.items():
        if old_pvm[0] not in reversed_pvms:
            reversed_pvms[old_pvm[0]] = (old_pvm[1],)
        else:
            reversed_pvms[old_pvm[0]] = reversed_pvms[old_pvm[0]] + (old_pvm[1],)
    return reversed_pvms


def get_reversed_pvm_map(pvm_map: PvmMigrationMapType) -> PvmMigrationMapType:
    reversed_pvm_map: PvmMigrationMapType = {}
    for old_pvm, new_pvms in pvm_map.items():
        for new_pvm in new_pvms:
            if new_pvm not in reversed_pvm_map:
                reversed_pvm_map[new_pvm] = (old_pvm,)
            else:
                reversed_pvm_map[new_pvm] = reversed_pvm_map[new_pvm] + (old_pvm,)
    return reversed_pvm_map
