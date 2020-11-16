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
import React, { useState, useMemo } from 'react';
import { t } from '@superset-ui/core';
import { useListViewResource, useFavoriteStatus } from 'src/views/CRUD/hooks';
import withToasts from 'src/messageToasts/enhancers/withToasts';
import { User } from 'src/types/bootstrapTypes';
import Icon from 'src/components/Icon';
import ChartCard from 'src/views/CRUD/chart/ChartCard';
import Chart from 'src/types/Chart';
import SubMenu from 'src/components/Menu/SubMenu';
import EmptyState from './EmptyState';
import { CardContainer, IconContainer } from '../utils';

const PAGE_SIZE = 3;

interface ChartTableProps {
  addDangerToast: (message: string) => void;
  addSuccessToast: (message: string) => void;
  search: string;
  chartFilter?: string;
  user?: User;
  mine: Array<any>;
}

function ChartTable({
  user,
  addDangerToast,
  addSuccessToast,
  mine,
}: ChartTableProps) {
  const {
    state: { resourceCollection: charts, bulkSelectEnabled },
    hasPerm,
    refreshData,
    fetchData,
  } = useListViewResource<Chart>(
    'chart',
    t('chart'),
    addDangerToast,
    true,
    mine,
  );
  const chartIds = useMemo(() => charts.map(c => c.id), [charts]);
  const [saveFavoriteStatus, favoriteStatus] = useFavoriteStatus(
    'chart',
    chartIds,
    addDangerToast,
  );

  const [chartFilter, setChartFilter] = useState('Mine');

  const getFilters = (filterName: string) => {
    const filters = [];

    if (filterName === 'Mine') {
      filters.push({
        id: 'created_by',
        operator: 'rel_o_m',
        value: `${user?.userId}`,
      });
    } else {
      filters.push({
        id: 'id',
        operator: 'chart_is_fav',
        value: true,
      });
    }
    return filters;
  };

  const getData = (filter: string) => {
    return fetchData({
      pageIndex: 0,
      pageSize: PAGE_SIZE,
      sortBy: [
        {
          id: 'changed_on_delta_humanized',
          desc: true,
        },
      ],
      filters: getFilters(filter),
    });
  };

  return (
    <>
      <SubMenu
        activeChild={chartFilter}
        // eslint-disable-next-line react/no-children-prop
        tabs={[
          {
            name: 'Favorite',
            label: t('Favorite'),
            onClick: () =>
              getData('Favorite').then(() => setChartFilter('Favorite')),
          },
          {
            name: 'Mine',
            label: t('Mine'),
            onClick: () => getData('Mine').then(() => setChartFilter('Mine')),
          },
        ]}
        buttons={[
          {
            name: (
              <IconContainer>
                <Icon name="plus-small" />
                {t('Chart')}
              </IconContainer>
            ),
            buttonStyle: 'tertiary',
            onClick: () => {
              window.location.href = '/chart/add';
            },
          },
          {
            name: 'View All »',
            buttonStyle: 'link',
            onClick: () => {
              window.location.href = '/chart/list';
            },
          },
        ]}
      />
      {charts?.length ? (
        <CardContainer>
          {charts.map(e => (
            <ChartCard
              key={`${e.id}`}
              chartFilter={chartFilter}
              chart={e}
              userId={user?.userId}
              hasPerm={hasPerm}
              bulkSelectEnabled={bulkSelectEnabled}
              refreshData={refreshData}
              addDangerToast={addDangerToast}
              addSuccessToast={addSuccessToast}
              favoriteStatus={favoriteStatus[e.id]}
              saveFavoriteStatus={saveFavoriteStatus}
            />
          ))}
        </CardContainer>
      ) : (
        <EmptyState tableName="CHARTS" tab={chartFilter} />
      )}
    </>
  );
}

export default withToasts(ChartTable);
