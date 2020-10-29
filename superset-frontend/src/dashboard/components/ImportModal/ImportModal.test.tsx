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
import React, { FormEvent } from 'react';
import { shallow } from 'enzyme';
import ImportModal from 'src/dashboard/components/ImportModal';
import { FormControl, Button } from 'react-bootstrap';
import sinon from 'sinon';

const requiredProps = {
  onSubmit: () => {},
  onHide: () => {},
  onFileSelect: () => {},
};

const formEvent = {
  preventDefault: () => {},
  stopPropagation: () => {},
} as FormEvent<HTMLFormElement>;

const inputEvent: unknown = { target: { value: 'foo' } };

describe('ImportModal', () => {
  it('sets up default state', () => {
    const wrapper = shallow(<ImportModal {...requiredProps} show />);
    expect(wrapper.instance().state).toEqual({
      dashboardFile: undefined,
    });
  });

  describe('changeFile', () => {
    it('should update state', () => {
      const wrapper = shallow<ImportModal>(
        <ImportModal {...requiredProps} show />,
      );

      wrapper.instance().changeFile(inputEvent as FormEvent<FormControl>);
      expect(wrapper.instance().state).toEqual({
        dashboardFile: undefined,
      });
    });
  });
  describe('submit', () => {
    it('should call props.onSubmit', () => {
      const submitSpy = sinon.spy();
      const wrapper = shallow<ImportModal>(
        <ImportModal show {...requiredProps} onSubmit={submitSpy} />,
      );
      const mockFile = jest.fn() as unknown;

      wrapper.instance().setState({ dashboardFile: mockFile as File });

      wrapper.instance().submit(formEvent);
      expect(submitSpy.firstCall.args[0]).toEqual(mockFile);
    });
  });
  describe('onCancel', () => {
    it('should clear out the file state', () => {
      const wrapper = shallow<ImportModal>(
        <ImportModal {...requiredProps} show />,
      );
      const mockFile = jest.fn() as unknown;

      wrapper.instance().setState({ dashboardFile: mockFile as File });
      expect(wrapper.instance().state.dashboardFile).toEqual(mockFile);
      wrapper.instance().onCancel(inputEvent as React.MouseEvent<Button>);
      expect(wrapper.instance().state.dashboardFile).toBeUndefined();
    });
    it('should call onHide', () => {
      const onHideSpy = sinon.spy();
      const wrapper = shallow<ImportModal>(
        <ImportModal show {...requiredProps} onHide={onHideSpy} />,
      );

      wrapper.instance().onCancel(inputEvent as React.MouseEvent<Button>);
      expect(onHideSpy.firstCall.args[0]).toEqual(inputEvent);
    });
  });
});
