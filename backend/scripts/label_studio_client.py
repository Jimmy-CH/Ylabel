
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
            headers={**self.headers, "Content-Type": "application/json"}
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
            headers={**self.headers, "Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def build_annotation_result_from_json(self, seg_datas: List[Dict]) -> List[Dict]:
        result = []
        for i, seg_data in enumerate(seg_datas):
            start_ms, end_ms = seg_data["seg"]
            # 拼接文本：去除空格（如 "你 好" → "你好"）
            text_str = "".join(seg_data["text"].split())
            start_sec = start_ms / 1000.0
            end_sec = end_ms / 1000.0
            duration_sec = end_sec - start_sec

            anno_id = f"seg_{i}"

            # Labels 区域
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

            # Transcription
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
        """
        通过音频文件名（basename）在 Label Studio 项目中查找对应的 task_id

        :param project_id: 项目 ID
        :param audio_file_path: 本地音频文件路径（用于提取 basename）
        :param max_retries: 查询重试次数（应对 reimport 异步延迟）
        :return: task_id
        """
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
            # 查找匹配的 task
            for task in all_tasks:
                print('task', task)
                # audio_path = task.get("data", {}).get("audio", "")
                data_values = task.get("data", {}).values()
                for audio_path in data_values:
                    task_filename = os.path.basename(str(audio_path))
                    print('task_filename', task_filename)
                    if task_filename.split('-', 1)[1] == target_filename:
                        return task["id"]

            # 如果没找到，等待后重试（reimport 可能是异步的）
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

        # Step 1: Upload
        import_resp = self.import_file(project_id, audio_file_path, commit_to_project=False)
        file_upload_ids = [item for item in import_resp.get('file_upload_ids', [])]
        if not file_upload_ids:
            raise ValueError("No file uploaded.")
        # 注意：这里不再使用 file_upload_id 作为 task_id

        # Step 2: Reimport to create task(s)
        self.reimport(project_id, file_upload_ids)

        # Step 3: Get real task_id by filename (with retry)
        task_id = self.get_task_id_by_filename(project_id, audio_file_path)
        print(f" Found task_id: {task_id}")

        # Step 4: Build annotation
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

        # Step 5: Submit
        anno_resp = self.submit_annotation(task_id, project_id, annotation_payload)
        return {"task_id": task_id, "annotation": anno_resp}

    def process_jsonl_file(
            self,
            project_id: int,
            jsonl_path: str,
            skip_missing_wav: bool = True,
            max_records: Optional[int] = None
    ):
        """
        批量处理 jsonl 文件中的所有记录
        :param project_id: Label Studio 项目 ID
        :param jsonl_path: .jsonl 文件路径
        :param skip_missing_wav: 是否跳过音频文件不存在的记录
        :param max_records: 最大处理条数（用于测试）
        """
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

                    # Process this record
                    self.run_full_pipeline_with_json(project_id, wav_path, data)
                    success_count += 1
                    print(f"[Line {line_num}] Success\n")

                except Exception as e:
                    import traceback
                    print(f"[Line {line_num}] Error: {e}")
                    print("Traceback (most recent call last):")
                    traceback.print_exc()
                    print()  # 空行分隔

        print(f"\n Processing completed!")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")


# 使用示例
if __name__ == "__main__":
    client = LabelStudioClient(
        base_url="http://10.130.11.184:8000/",
        sessionid=".eJxVT8uOgyAU_RfWSuACAi67n28gCBdlaqARTaadzL9Pbbrp8rxzfsmRIxlJQqslV6wHTLyXiUHvhxB6bpWJAkISMZGO1G32JT_8nmtxtysZeUdW33a31jmXJ9SD4dpyLinTfABtO-L8sS_uaLi519RAPrjJhyuWU4jfvsyVhlr2LU_0tNC32uhXjbhe3t6PgsW35ZmW1mDUAEFCACMNKAGohI026cgShhAMQtLcWqPNBGxAprzwUmgJKF-lDVs7n-HPLW93MoKywBhlf__R0Ft_:1vgGGv:UDNTU32Ht6WOUOpI_GmNfd_zmUfmAIi0qlb50lrDk2U",
        csrftoken="GSlBrDnYVkartJxKe5tFRNexKYiwCf8v",
        auth_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mbyI6eyJ1c2VyQ29kZSI6IjAzNDIwMDkyIiwidXNlck5hbWUiOiLpmYjlhYkiLCJ1c2VyQ2xpZW50SWQiOiJQQy1YRC1TRVJWRVIiLCJleHRlbmRBdHRyaWJ1dGVzIjp7InVzZXJDaGFubmVsIjoiSFIiLCJ1c2VyTWFyayI6IkhSX0VYUFJFU1MifSwicmVsYXRpb25MaXN0IjpudWxsLCJtdWx0aU9yZ1ZPIjpudWxsfSwibG9naW5UaW1lIjoxNzY3NzcxNDI1LCJncmFudF90eXBlIjoieXRvX3RnYyIsInVzZXJfbmFtZSI6IjAzNDIwMDkyIiwic2NvcGUiOlsic2VydmVyIl0sImV4cCI6MTc2Nzc3ODYyNSwianRpIjoiMDA2MWI5YWEtZDU2NC00ZmU4LTg3M2ItYTExOTQ5MjkxZjU4IiwiY2xpZW50X2lkIjoiUEMtWEQtU0VSVkVSIn0.IaNcNTsbVoxdV8ZlZKMNpqKJRX3jjNSfuz0WVNIjeC0ssY-FwRCChETdcF5RR5ZrFtucpIwPdKAfF6h9bBE75wnfL7J7LoYF858IAo28md-g2kbueY4jPrHZMwaDIvxp5lfQSUOy0sXzLwhMiHoLnR7F-g8PcopgdfgfyF9N4Z0"
    )

    try:
        client.process_jsonl_file(
            project_id=1,
            jsonl_path="./data.jsonl",
            skip_missing_wav=True,
            max_records=None       # 设置为 5 可测试前5条
        )
    except Exception as e:
        print(f"Fatal error: {e}")
