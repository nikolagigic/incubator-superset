import { SupersetClient, JsonResponse } from '@superset-ui/core';
import rison from 'rison';

export const post = async (dashboardFile: File) => {
  const endpoint = encodeURI(`/api/v1/dashboard/import/`);
  const formData = new FormData();
  formData.append('formData', dashboardFile);
  await SupersetClient.post({
    endpoint,
    body: formData,
  });
  return Promise.resolve();
};

export const get = async () => {
  const queryParams = rison.encode({
    order_column: 'changed_on_delta_humanized',
    order_direction: 'desc',
    page: 0,
    page_size: 10,
  });
  const endpoint = `/api/v1/dashboard?q=${queryParams}`;
  const json: JsonResponse = await SupersetClient.get({
    endpoint,
  });
  return Promise.resolve(json.json.result);
};
