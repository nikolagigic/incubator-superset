import { SupersetClient, JsonResponse } from '@superset-ui/core';
import rison from 'rison';

export const importDataset = async (datasetFile: File) => {
  const endpoint = encodeURI(`/api/v1/dataset/import/`);
  const formData = new FormData();
  formData.append('formData', datasetFile);
  const response: JsonResponse = await SupersetClient.post({
    endpoint,
    body: formData,
  });
  return Promise.resolve(response);
};

export const get = async () => {
  const queryParams = rison.encode({
    order_column: 'changed_on_delta_humanized',
    order_direction: 'desc',
    page: 0,
    page_size: 10,
  });
  const endpoint = `/api/v1/dataset?q=${queryParams}`;
  const json: JsonResponse = await SupersetClient.get({
    endpoint,
  });
  return Promise.resolve(json.json.result);
};
