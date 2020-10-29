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
import React from 'react';
import { mount } from 'enzyme';
import fetchMock from 'fetch-mock';
import { Provider } from 'react-redux';
import { supersetTheme, ThemeProvider } from '@superset-ui/core';
import * as featureFlags from 'src/featureFlags';
import { mockStore } from 'spec/fixtures/mockStore';

import ImportModal from 'src/dashboard/components/ImportModal';
import DashboardList from './DashboardList';

const dashboardInfoEndpoint = 'glob:*/api/v1/dashboard/_info*';

fetchMock.get(dashboardInfoEndpoint, {
  permissions: ['can_add', 'can_edit', 'can_delete'],
});

describe('DashboardList', () => {
  beforeAll(() => {
    jest.spyOn(featureFlags, 'isFeatureEnabled').mockImplementation(() => true);
  });

  afterAll(() => {
    jest.restoreAllMocks();
  });

  describe('dashboard import', () => {
    describe('on load', () => {
      it('modal should be hidden', () => {
        const wrapper = mount(
          <Provider store={mockStore}>
            <ThemeProvider theme={supersetTheme}>
              <DashboardList />
            </ThemeProvider>
          </Provider>,
        );
        expect(wrapper.find(ImportModal)).toEqual('foo');
      });
    });
    describe('when import button is clicked', () => {
      it('import modal should be visible', () => {
        const wrapper = mount(
          <Provider store={mockStore}>
            <ThemeProvider theme={supersetTheme}>
              <DashboardList />
            </ThemeProvider>
          </Provider>,
        );
        const dashboard = wrapper.find('[data-test="import-dashboard-button"]');
        expect(dashboard.find('SubMenu')).toEqual('foo');
      });
    });
  });
});
