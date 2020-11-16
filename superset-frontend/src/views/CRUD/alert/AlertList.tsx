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

import React, { useState } from 'react';
import { t } from '@superset-ui/core';
import SubMenu, { SubMenuProps } from 'src/components/Menu/SubMenu';
import withToasts from 'src/messageToasts/enhancers/withToasts';
import AlertReportModal from './AlertReportModal';

import { AlertObject } from './types';

interface AlertListProps {
  addDangerToast: (msg: string) => void;
  addSuccessToast: (msg: string) => void;
}

function AlertList({ addDangerToast, addSuccessToast }: AlertListProps) {
  const [alertModalOpen, setAlertModalOpen] = useState<boolean>(false);

  const [currentAlert, setCurrentAlert] = useState<AlertObject | null>(null);

  // Actions
  function handleAlertEdit(alert: AlertObject | null) {
    setCurrentAlert(alert);
    setAlertModalOpen(true);
  }

  const subMenuButtons: SubMenuProps['buttons'] = [];

  subMenuButtons.push({
    name: (
      <>
        <i className="fa fa-plus" /> {t('Alert')}
      </>
    ),
    buttonStyle: 'primary',
    onClick: () => {
      handleAlertEdit(null);
    },
  });

  return (
    <>
      <SubMenu
        activeChild="Alerts"
        name={t('Alerts & Reports')}
        tabs={[
          {
            name: 'Alerts',
            label: t('Alerts'),
            url: '/alerts/list/',
            usesRouter: true,
          },
          {
            name: 'Reports',
            label: t('Reports'),
            url: '/reports/list/',
            usesRouter: true,
          },
        ]}
        buttons={subMenuButtons}
      />
      <AlertReportModal
        addDangerToast={addDangerToast}
        layer={currentAlert}
        onHide={() => setAlertModalOpen(false)}
        show={alertModalOpen}
      />
    </>
  );
}

export default withToasts(AlertList);
