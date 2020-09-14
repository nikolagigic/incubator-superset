/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import React, { SVGProps } from 'react';
import { ReactComponent as CancelXIcon } from 'images/icons/cancel-x.svg';
import { ReactComponent as CardViewIcon } from 'images/icons/card_view.svg';
import { ReactComponent as CertifiedIcon } from 'images/icons/certified.svg';
import { ReactComponent as CheckboxHalfIcon } from 'images/icons/checkbox-half.svg';
import { ReactComponent as CheckboxOffIcon } from 'images/icons/checkbox-off.svg';
import { ReactComponent as CheckboxOnIcon } from 'images/icons/checkbox-on.svg';
import { ReactComponent as CheckIcon } from 'images/icons/check.svg';
import { ReactComponent as CircleCheckIcon } from 'images/icons/circle_check.svg';
import { ReactComponent as CircleCheckSolidIcon } from 'images/icons/circle_check_solid.svg';
import { ReactComponent as CloseIcon } from 'images/icons/close.svg';
import { ReactComponent as NavExploreIcon } from 'images/icons/nav_explore.svg';
import { ReactComponent as DatabaseIcon } from 'images/icons/database.svg';
import { ReactComponent as DatasetPhysicalIcon } from 'images/icons/dataset_physical.svg';
import { ReactComponent as DatasetVirtualIcon } from 'images/icons/dataset_virtual.svg';
import { ReactComponent as DropdownArrowIcon } from 'images/icons/dropdown-arrow.svg';
import { ReactComponent as ErrorSolidIcon } from 'images/icons/error_solid.svg';
import { ReactComponent as FavoriteSelectedIcon } from 'images/icons/favorite-selected.svg';
import { ReactComponent as FavoriteUnselectedIcon } from 'images/icons/favorite-unselected.svg';
import { ReactComponent as ListViewIcon } from 'images/icons/list_view.svg';
import { ReactComponent as MoreHorizIcon } from 'images/icons/more_horiz.svg';
import { ReactComponent as EditAltIcon } from 'images/icons/edit_alt.svg';
import { ReactComponent as SearchIcon } from 'images/icons/search.svg';
import { ReactComponent as ShareIcon } from 'images/icons/share.svg';
import { ReactComponent as SortAscIcon } from 'images/icons/sort_asc.svg';
import { ReactComponent as SortDescIcon } from 'images/icons/sort_desc.svg';
import { ReactComponent as SortIcon } from 'images/icons/sort.svg';
import { ReactComponent as TrashIcon } from 'images/icons/trash.svg';
import { ReactComponent as WarningSolidIcon } from 'images/icons/warning_solid.svg';

type IconName =
  | 'cancel-x'
  | 'card-view'
  | 'certified'
  | 'check'
  | 'checkbox-half'
  | 'checkbox-off'
  | 'checkbox-on'
  | 'circle-check-solid'
  | 'circle-check'
  | 'close'
  | 'nav-explore'
  | 'database'
  | 'dataset-physical'
  | 'dataset-virtual'
  | 'dropdown-arrow'
  | 'error-solid'
  | 'favorite-selected'
  | 'favorite-unselected'
  | 'list-view'
  | 'more-horiz'
  | 'edit-alt'
  | 'search'
  | 'share'
  | 'sort-asc'
  | 'sort-desc'
  | 'sort'
  | 'trash'
  | 'warning-solid';

export const iconsRegistry: Record<
  IconName,
  React.ComponentType<SVGProps<SVGSVGElement>>
> = {
  'cancel-x': CancelXIcon,
  'card-view': CardViewIcon,
  'checkbox-half': CheckboxHalfIcon,
  'checkbox-off': CheckboxOffIcon,
  'checkbox-on': CheckboxOnIcon,
  'circle-check-solid': CircleCheckSolidIcon,
  'circle-check': CircleCheckIcon,
  database: DatabaseIcon,
  'dataset-physical': DatasetPhysicalIcon,
  'dataset-virtual': DatasetVirtualIcon,
  'favorite-selected': FavoriteSelectedIcon,
  'favorite-unselected': FavoriteUnselectedIcon,
  'list-view': ListViewIcon,
  'dropdown-arrow': DropdownArrowIcon,
  'sort-asc': SortAscIcon,
  'sort-desc': SortDescIcon,
  certified: CertifiedIcon,
  check: CheckIcon,
  close: CloseIcon,
  'nav-explore': NavExploreIcon,
  'error-solid': ErrorSolidIcon,
  'more-horiz': MoreHorizIcon,
  "edit-alt": EditAltIcon,
  search: SearchIcon,
  share: ShareIcon,
  sort: SortIcon,
  trash: TrashIcon,
  'warning-solid': WarningSolidIcon,
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
}

const Icon = ({
  name,
  color = '#666666',
  viewBox = '0 0 24 24',
  ...rest
}: IconProps) => {
  const Component = iconsRegistry[name];

  return (
    <Component color={color} viewBox={viewBox} data-test={name} {...rest} />
  );
};

export default Icon;
