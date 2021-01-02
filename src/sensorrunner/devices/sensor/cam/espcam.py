from urllib.parse import urlencode
import json
import requests
import datetime

# def get_image(bucket, index, ts):
#     qs_dict = {"bucket": bucket, "index": index, "ts": ts}
#     r_url, r_header, r_payload = _v1_req_adapter(
#         api_endpoint="retrieve", qs_dict=qs_dict
#     )
#     r_method = "GET"
#     rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
#     return rd


# def capture_image(bucket, index, ts):
#     data_dict = {"cam": {"bucket": bucket, "index": index, "ts": ts}}
#     r_url, r_header, r_payload = _v1_req_adapter(
#         api_endpoint="capture", data_dict=data_dict
#     )
#     r_method = "POST"
#     rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
#     return rd


# def list_sd_files():
#     r_url, r_header, r_payload = _v1_req_adapter(api_endpoint="sdfiles")
#     r_method = "GET"
#     rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
#     return rd


# def delete_sd_image(bucket, index, ts):
#     qs_dict = {"bucket": bucket, "index": index, "ts": ts}
#     r_url, r_header, r_payload = _v1_req_adapter(
#         api_endpoint="sdfiles", qs_dict=qs_dict
#     )
#     r_method = "DELETE"
#     rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
#     return rd


# def status():
#     r_url, r_header, r_payload = _v1_req_adapter(api_endpoint="status")
#     r_method = "GET"
#     rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
#     return rd


class ESPCam:
    def __init__(self, ip_addr=None):
        if ip_addr is None:
            raise ValueError(f"ip_addr must be specified")
        self.ip_addr = ip_addr
        self.path_template = "{}__{}__{}.jpg"

    def _build_req(self, ip_addr, port, api_v, api_endpoint, qs_dict, data_dict):
        URL = f"http://{ip_addr}:{port}/api/{api_v}/{api_endpoint}"

        if qs_dict is not None:
            qstr = urlencode(qs_dict)
            URL = f"{URL}?{qstr}"

        if data_dict:
            data_payload = json.dumps(data_dict)
            headers = {"Content-Type": "application/json"}
        else:
            data_payload = None
            headers = None

        return (URL, headers, data_payload)

    def _v1_req_adapter(
        self,
        ip_addr,
        port_str,
        api_endpoint,
        api_v="v1",
        qs_dict=None,
        data_dict=None,
    ):
        if data_dict is None:
            data_dict = {}
        r_url, r_header, r_payload = self._build_req(
            ip_addr=ip_addr,
            port=port_str,
            api_v=api_v,
            api_endpoint=api_endpoint,
            qs_dict=qs_dict,
            data_dict=data_dict,
        )
        return r_url, r_header, r_payload

    def obtain_image_rd(self, bucket, index, ts):
        # url = "http://<>/api/v1/obtain?index=0&ts=01_01_2021__13_52_10&bucket=0"
        qs_dict = {"bucket": bucket, "index": index, "ts": ts}
        r_url, r_header, r_payload = self._v1_req_adapter(
            api_endpoint="obtain", qs_dict=qs_dict
        )
        r_method = "GET"
        rd = {"method": r_method, "url": r_url, "headers": r_header, "data": r_payload}
        return rd

    def _write_resp_image(self, local_dir, local_fname, response):
        file_path = f"{local_dir}/{local_fname}"
        with open(file_path, "wb") as fp:
            for chunk in response:
                fp.write(chunk)
        return file_path

    def return_value(self, **kwargs):
        try:
            bucket = kwargs["bucket"]
        except KeyError:
            raise ValueError(f"bucket not in {kwargs}")

        try:
            index = kwargs["index"]
        except KeyError:
            raise ValueError(f"index not in {kwargs}")

        # e.g. '01_01_2021__17_13_18'
        ts = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")

        try:
            local_dir = kwargs["local_dir"]
        except KeyError:
            raise ValueError(f"local_dir not in {kwargs}")
        local_fname = self.path_template.format(bucket, index, ts)

        # stream=True
        req_dict = self.obtain_image_rd(bucket, index, ts)
        response = requests.request(**req_dict)
        # ConnectionError
        if response.status_code == 200:
            local_file_path = self._write_resp_image(local_dir, local_fname, response)
        else:
            raise ValueError(
                f"unable to obtain image: {response.status_code} \n{response}"
            )

        val_d = {"image_path": local_file_path, "capture_time": ts}

        return val_d
