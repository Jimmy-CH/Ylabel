import os
import json
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime


class LabelStudioClient:
    def __init__(
            self,
            base_url: str,
            sessionid: str,
            csrftoken: str,
            auth_token: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.sessionid = sessionid
        self.csrftoken = csrftoken
        self.auth_token = auth_token

        self.cookies = {
            "sessionid": sessionid,
            "csrftoken": csrftoken,
        }
        self.headers = {
            "X-CSRFToken": csrftoken,
        }
        if auth_token:
            self.headers["Authorization"] = auth_token

    def _make_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        headers = self.headers.copy()
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def get_project_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        根据项目标题查询项目信息。
        :param title: 项目标题
        :return: 项目字典（若存在），否则 None
        """
        url = f"{self.base_url}/api/projects/"
        params = {"title": title}
        response = requests.get(
            url,
            params=params,
            cookies=self.cookies,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        projects = data.get("results", []) if "results" in data else data  # 兼容分页/不分页
        if isinstance(projects, list) and len(projects) > 0:
            return projects[0]
        return None

    def create_project(
            self,
            title: str,
            label_config: str,
            description: str = "",
            is_draft: bool = True
    ) -> Dict[str, Any]:
        """
        创建新项目。
        :param title: 项目标题
        :param label_config: Label Studio 标注配置（XML 字符串）
        :param description: 描述（可选）
        :param is_draft: 是否为草稿
        :return: 创建的项目信息
        """
        url = f"{self.base_url}/api/projects/"
        payload = {
            "title": title,
            "description": description,
            "label_config": label_config,
            "is_draft": is_draft
        }
        response = requests.post(
            url,
            json=payload,
            cookies=self.cookies,
            headers=self._make_headers("application/json")
        )
        response.raise_for_status()
        return response.json()

    def ensure_project(
            self,
            title: str,
            label_config: str,
            description: str = "Auto-created by script",
            is_draft: bool = True
    ) -> int:
        """
        确保项目存在：若存在则返回其 ID；若不存在则创建并返回新 ID。
        :return: project_id (int)
        """
        project = self.get_project_by_title(title)
        if project:
            print(f"Project '{title}' already exists with ID: {project['id']}")
            return project["id"]
        else:
            print(f"Project '{title}' not found. Creating...")
            new_project = self.create_project(title, label_config, description, is_draft)
            print(f"Created project '{title}' with ID: {new_project['id']}")
            return new_project["id"]

    # 以下是原有方法

    def import_file(self, project_id: int, file_path: str, commit_to_project: bool = False) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base_url}/api/projects/{project_id}/import"
        params = {"commit_to_project": str(commit_to_project).lower()}

        with open(file_path, 'rb') as f:
            files = {'files': f}
            response = requests.post(
                url,
                params=params,
                cookies=self.cookies,
                headers=self.headers,
                files=files
            )

        response.raise_for_status()
        return response.json()

    def reimport(
            self,
            project_id: int,
            file_upload_ids: List[int],
            files_as_tasks_list: bool = False
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/projects/{project_id}/reimport"
        payload = {
            "file_upload_ids": file_upload_ids,
            "files_as_tasks_list": files_as_tasks_list
        }

        response = requests.post(
            url,
            json=payload,
            cookies=self.cookies,
            headers=self._make_headers("application/json")
        )
        response.raise_for_status()
        return response.json()

    def submit_annotation(
            self,
            task_id: int,
            project_id: int,
            annotation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/tasks/{task_id}/annotations/"
        params = {"project": str(project_id)}

        response = requests.post(
            url,
            params=params,
            json=annotation_data,
            cookies=self.cookies,
            headers=self._make_headers("application/json")
        )
        response.raise_for_status()
        return response.json()

    def build_annotation_result_from_json(self, seg_datas: List[Dict]) -> List[Dict]:
        result = []
        for i, seg_data in enumerate(seg_datas):
            start_ms, end_ms = seg_data["seg"]
            text_str = "".join(seg_data["text"].split())
            start_sec = start_ms / 1000.0
            end_sec = end_ms / 1000.0
            duration_sec = end_sec - start_sec
            anno_id = f"seg_{i}"

            result.append({
                "original_length": duration_sec,
                "value": {
                    "start": start_sec,
                    "end": end_sec,
                    "channel": 0,
                    "labels": ["Speech"]
                },
                "id": anno_id,
                "from_name": "labels",
                "to_name": "audio",
                "type": "labels",
                "origin": "manual"
            })

            result.append({
                "original_length": duration_sec,
                "value": {
                    "start": start_sec,
                    "end": end_sec,
                    "channel": 0,
                    "text": [text_str]
                },
                "id": anno_id,
                "from_name": "transcription",
                "to_name": "audio",
                "type": "textarea",
                "origin": "manual"
            })
        return result

    def get_task_id_by_filename(self, project_id: int, audio_file_path: str, max_retries: int = 5) -> int:
        target_filename = os.path.basename(audio_file_path)
        print('target_filename', target_filename)
        url = f"{self.base_url}/api/tasks/"
        params = {
            "project": str(project_id),
            "page_size": 100
        }

        for attempt in range(max_retries):
            all_tasks = []
            page = 1
            while True:
                params["page"] = page
                response = requests.get(
                    url,
                    params=params,
                    cookies=self.cookies,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                tasks = data.get("tasks", [])
                if not tasks:
                    break
                all_tasks.extend(tasks)
                if len(tasks) < params["page_size"]:
                    break
                page += 1

            for task in all_tasks:
                data_values = task.get("data", {}).values()
                for audio_path in data_values:
                    task_filename = os.path.basename(str(audio_path))
                    if task_filename.split('-', 1)[-1] == target_filename:  # 修复：防止索引错误
                        return task["id"]

            if attempt < max_retries - 1:
                import time
                print(f"Task not found for '{target_filename}', retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2)

        raise ValueError(f"Task not found for audio file: {target_filename} after {max_retries} retries.")

    def run_full_pipeline_with_json(
            self,
            project_id: int,
            audio_file_path: str,
            json_data: Dict[str, Any]
    ):
        print(f"Processing: {os.path.basename(audio_file_path)}")

        import_resp = self.import_file(project_id, audio_file_path, commit_to_project=False)
        file_upload_ids = import_resp.get('file_upload_ids', [])
        if not file_upload_ids:
            raise ValueError("No file uploaded.")

        self.reimport(project_id, file_upload_ids)
        task_id = self.get_task_id_by_filename(project_id, audio_file_path)
        print(f" Found task_id: {task_id}")

        seg_datas = (json_data.get("ref_anno") or {}).get("seg_datas") or \
                    (json_data.get("model_anno") or {}).get("seg_datas")
        if not seg_datas:
            raise ValueError("No segmentation data.")

        annotation_result = self.build_annotation_result_from_json(seg_datas)

        annotation_payload = {
            "lead_time": json_data.get("dur", 0.0),
            "result": annotation_result,
            "parent_prediction": None,
            "parent_annotation": None,
            "started_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "project": str(project_id)
        }

        anno_resp = self.submit_annotation(task_id, project_id, annotation_payload)
        return {"task_id": task_id, "annotation": anno_resp}

    def process_jsonl_file(
            self,
            project_id: int,
            jsonl_path: str,
            skip_missing_wav: bool = True,
            max_records: Optional[int] = None
    ):
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

        success_count = 0
        error_count = 0

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if max_records and line_num > max_records:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    wav_path = data.get("wav")
                    if not wav_path:
                        print(f"[Line {line_num}]  Missing 'wav' field. Skipped.")
                        error_count += 1
                        continue

                    if not os.path.exists(wav_path):
                        msg = f"[Line {line_num}]  WAV not found: {wav_path}"
                        if skip_missing_wav:
                            print(msg + " (Skipped)")
                            error_count += 1
                            continue
                        else:
                            raise FileNotFoundError(msg)

                    self.run_full_pipeline_with_json(project_id, wav_path, data)
                    success_count += 1
                    print(f"[Line {line_num}] Success\n")

                except Exception as e:
                    import traceback
                    print(f"[Line {line_num}] Error: {e}")
                    traceback.print_exc()
                    print()

        print(f"\n Processing completed!")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")

    def create_default_view(self, project_id: int) -> Dict[str, Any]:
        """
        为指定项目创建一个默认数据管理视图（Data Manager View）。
        模拟 Postman 请求：POST /api/dm/views?tabID=0&project={project_id}
        """
        url = f"{self.base_url}/api/dm/views"
        params = {
            "tabID": "0",
            "project": str(project_id)
        }

        view_data = {
            "title": "Default",
            "ordering": [],
            "type": "list",
            "target": "tasks",
            "filters": {
                "conjunction": "and",
                "items": []
            },
            "hiddenColumns": {
                "explore": [
                    "tasks:inner_id",
                    "tasks:annotations_results",
                    "tasks:annotations_ids",
                    "tasks:predictions_score",
                    "tasks:predictions_model_versions",
                    "tasks:predictions_results",
                    "tasks:file_upload",
                    "tasks:storage_filename",
                    "tasks:created_at",
                    "tasks:updated_at",
                    "tasks:updated_by",
                    "tasks:avg_lead_time",
                    "tasks:draft_exists"
                ],
                "labeling": [
                    "tasks:id",
                    "tasks:inner_id",
                    "tasks:completed_at",
                    "tasks:cancelled_annotations",
                    "tasks:total_predictions",
                    "tasks:annotators",
                    "tasks:annotations_results",
                    "tasks:annotations_ids",
                    "tasks:predictions_score",
                    "tasks:predictions_model_versions",
                    "tasks:predictions_results",
                    "tasks:file_upload",
                    "tasks:storage_filename",
                    "tasks:created_at",
                    "tasks:updated_at",
                    "tasks:updated_by",
                    "tasks:avg_lead_time",
                    "tasks:draft_exists"
                ]
            },
            "columnsWidth": {},
            "columnsDisplayType": {},
            "gridWidth": 4,
            "gridFitImagesToWidth": False,
            "semantic_search": [],
            "agreement_selected": {}
        }

        payload = {
            "data": view_data,
            "project": str(project_id)
        }

        response = requests.post(
            url,
            params=params,
            json=payload,
            cookies=self.cookies,
            headers=self._make_headers("application/json")
        )
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = LabelStudioClient(
        # base_url="http://10.130.18.74:8080/",
        base_url="http://10.130.11.184:8000/",
        sessionid=".eJxVT0luhDAQ_IvPYHlt2xxzzxuQ227AGYRHGKQsyt8TRnNIjrWoli92lswGJsEkodD1pCn1xmLqcZKh92RkjkAJpGcdq_sct_IZj1K38X5jg-zYGtsxrnUu2y904L2wWjnupZLadGyM57GMZ6N9fDRdMX84jOlG2yXkt7jNlae6HXtBfln4U238tWZaX57efwFLbMt1QEKW4EBPNkaXpNA6IApjMqD21lg1BWcDIWYClIbAICnyIZAGiI9VjVq7jtH7vewfbFA2KCG4-P4BuANblg:1vincZ:azHqg2eKZn5D9ADnuLIw-6hYvebLYrxHU53brNPkhr4",
        csrftoken="fj5UiFAuLbZM0XF9hYHkvrQgkpejfRoW",
        auth_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mbyI6eyJ1c2VyQ29kZSI6IjAzNDIwMDkyIiwidXNlck5hbWUiOiLpmYjlhYkiLCJ1c2VyQ2xpZW50SWQiOiJQQy1YRC1TRVJWRVIiLCJleHRlbmRBdHRyaWJ1dGVzIjp7InVzZXJDaGFubmVsIjoiSFIiLCJ1c2VyTWFyayI6IkhSX0VYUFJFU1MifSwicmVsYXRpb25MaXN0IjpudWxsLCJtdWx0aU9yZ1ZPIjpudWxsfSwibG9naW5UaW1lIjoxNzY3NzcxNDI1LCJncmFudF90eXBlIjoieXRvX3RnYyIsInVzZXJfbmFtZSI6IjAzNDIwMDkyIiwic2NvcGUiOlsic2VydmVyIl0sImV4cCI6MTc2Nzc3ODYyNSwianRpIjoiMDA2MWI5YWEtZDU2NC00ZmU4LTg3M2ItYTExOTQ5MjkxZjU4IiwiY2xpZW50X2lkIjoiUEMtWEQtU0VSVkVSIn0.IaNcNTsbVoxdV8ZlZKMNpqKJRX3jjNSfuz0WVNIjeC0ssY-FwRCChETdcF5RR5ZrFtucpIwPdKAfF6h9bBE75wnfL7J7LoYF858IAo28md-g2kbueY4jPrHZMwaDIvxp5lfQSUOy0sXzLwhMiHoLnR7F-g8PcopgdfgfyF9N4Z0"
    )

    # 定义你的标注配置 以下为音频配置标准模板
    LABEL_CONFIG = """<View>
  <Labels name="labels" toName="audio">
    <Label value="Speech" />
    <Label value="Noise" />
  </Labels>

  <Audio name="audio" value="$audio" spectrogram="true"/>

  <TextArea name="transcription" toName="audio"
            rows="2" editable="true"
            perRegion="true" required="true" />
</View>"""

    # 自动获取或创建项目
    project_id = client.ensure_project(
        title="数据导入展示",
        label_config=LABEL_CONFIG,
        description="测试",
        is_draft=True
    )

    # 创建默认视图
    try:
        view_resp = client.create_default_view(project_id)
        print(f"Default view created for project {project_id}, view ID: {view_resp.get('id')}")
    except Exception as e:
        print(f"Failed to create default view: {e}")

    # 批量处理 JSONL
    try:
        client.process_jsonl_file(
            project_id=project_id,
            jsonl_path="./data.jsonl",
            skip_missing_wav=True,
            max_records=None
        )
    except Exception as e:
        print(f"Fatal error: {e}")

