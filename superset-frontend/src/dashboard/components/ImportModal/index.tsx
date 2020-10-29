// /**
//  * Licensed to the Apache Software Foundation (ASF) under one
//  * or more contributor license agreements.  See the NOTICE file
//  * distributed with this work for additional information
//  * regarding copyright ownership.  The ASF licenses this file
//  * to you under the Apache License, Version 2.0 (the
//  * "License"); you may not use this file except in compliance
//  * with the License.  You may obtain a copy of the License at
//  *
//  *   http://www.apache.org/licenses/LICENSE-2.0
//  *
//  * Unless required by applicable law or agreed to in writing,
//  * software distributed under the License is distributed on an
//  * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
//  * KIND, either express or implied.  See the License for the
//  * specific language governing permissions and limitations
//  * under the License.
//  */
import React, { PureComponent, FormEvent } from 'react';
import {
  Row,
  Col,
  Modal,
  FormControl,
  Alert,
  Button as BootstrapButton,
} from 'react-bootstrap';
import { styled, t } from '@superset-ui/core';

import FormLabel from 'src/components/FormLabel';
import Button, { OnClickHandler } from 'src/components/Button';

import '../../stylesheets/buttons.less';

const AlertWrapper = styled(Alert)`
  border-radius: 8px;
  margin-bottom: 8px;
  margin-top: 28px;
  border: 2px solid ${({ theme }) => theme.colors.error.light1};
  background-color: ${({ theme }) => theme.colors.error.light2};
  line-height: 24px;
  padding: 8px 12px;

  .alert-icon {
    color: ${({ theme }) => theme.colors.error.dark1};
    font-size: 20px;
    margin-right: 8px;
  }
`;

export interface DashboardProps {
  show?: boolean;
  onHide: OnClickHandler;
  onSubmit: Function;
  error?: string | null;
  onFileSelect: Function;
}

export interface DashboardState {
  dashboardFile?: File;
}

class ImportDashboardModal extends PureComponent<
  DashboardProps,
  DashboardState
> {
  static defaultProps = {
    show: false,
  };

  constructor(props: DashboardProps) {
    super(props);
    this.state = {
      dashboardFile: undefined,
    };
    this.changeFile = this.changeFile.bind(this);
    this.submit = this.submit.bind(this);
    this.onCancel = this.onCancel.bind(this);
  }

  onCancel(e: React.MouseEvent<BootstrapButton>) {
    this.setState({ dashboardFile: undefined });
    this.props.onHide(e);
  }

  changeFile(event: FormEvent<FormControl>) {
    const { files } = event.target as HTMLInputElement;
    this.setState({
      dashboardFile: (files && files[0]) || undefined,
    });
    this.props.onFileSelect();
  }

  submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    e.stopPropagation();
    const { dashboardFile } = this.state;
    this.props.onSubmit(dashboardFile);
  }

  render() {
    const { error, show } = this.props;

    return (
      <Modal
        show={show}
        onHide={this.onCancel}
        bsSize="lg"
        data-test="import-modal"
      >
        <form onSubmit={this.submit}>
          <Modal.Header closeButton>
            <Modal.Title>
              <div>
                <span className="float-left">{t('Import Dashboards')}</span>
              </div>
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={12}>
                <FormLabel htmlFor="embed-height">{t('File')}</FormLabel>
                <FormControl
                  data-test="dashboard-file-input"
                  name="dashboardFile"
                  type="file"
                  accept=".yaml,.json,.yml, .zip"
                  onChange={this.changeFile}
                />
              </Col>
            </Row>
            {!!error?.length && (
              <AlertWrapper key="import-dashboard-error" bsStyle="danger">
                <p>
                  <i className="alert-icon fa fa-exclamation-circle" />
                  <strong>Import Error</strong>
                </p>
                {error}
              </AlertWrapper>
            )}
          </Modal.Body>
          <Modal.Footer>
            <span className="float-right">
              <Button type="button" buttonSize="sm" onClick={this.onCancel} cta>
                {t('Cancel')}
              </Button>
              <Button
                type="submit"
                buttonSize="sm"
                buttonStyle="primary"
                className="m-r-5"
                disabled={!this.state.dashboardFile || !!error?.length}
                cta
              >
                Upload
              </Button>
            </span>
          </Modal.Footer>
        </form>
      </Modal>
    );
  }
}

export default ImportDashboardModal;
