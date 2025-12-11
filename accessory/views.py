import json
import os
import uuid
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


METADATA_FILE = os.path.join(settings.MEDIA_ROOT, "metadata.json")


def _ensure_media_dir():
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)


def _load_metadata():
    _ensure_media_dir()
    if not os.path.exists(METADATA_FILE):
        return {"org": [], "emp": []}
    with open(METADATA_FILE, "r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            return {"org": [], "emp": []}


def _save_metadata(data):
    _ensure_media_dir()
    with open(METADATA_FILE, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def _build_file_path(prefix, filename):
    directory = os.path.join(settings.MEDIA_ROOT, prefix)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, filename)


def _public_path(file_path):
    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
    return f"{settings.MEDIA_URL}{relative_path}".replace("\\", "/")


@csrf_exempt
def upload_org_attach(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    org_id = request.POST.get("orgId")
    attach_type = request.POST.get("attachType")
    upload = request.FILES.get("file")

    if not org_id or not attach_type or not upload:
        return JsonResponse({"success": False, "message": "orgId、attachType与文件均不能为空"}, status=400)

    filename = f"{org_id}_{attach_type}_{upload.name}"
    file_path = _build_file_path("org_attach", filename)
    with open(file_path, "wb+") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    metadata = _load_metadata()
    attach_id = str(uuid.uuid4())
    record = {
        "id": attach_id,
        "orgId": org_id,
        "attachType": attach_type,
        "fileName": upload.name,
        "filePath": _public_path(file_path),
        "fileSize": upload.size,
        "uploadTime": timezone.now().isoformat(),
    }
    metadata.setdefault("org", []).append(record)
    _save_metadata(metadata)

    return JsonResponse({"success": True, "data": record})


@csrf_exempt
def list_org_attach(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "只支持GET请求"}, status=405)

    org_id = request.GET.get("orgId")
    attach_type = request.GET.get("attachType")
    if not org_id:
        return JsonResponse({"success": False, "message": "orgId不能为空"}, status=400)

    metadata = _load_metadata()
    items = [item for item in metadata.get("org", []) if item.get("orgId") == org_id]
    if attach_type:
        items = [item for item in items if item.get("attachType") == attach_type]

    return JsonResponse({"success": True, "data": items})


@csrf_exempt
def delete_org_attach(request, attach_id):
    if request.method != "DELETE":
        return JsonResponse({"code": 405, "message": "只支持DELETE请求"}, status=405)

    metadata = _load_metadata()
    items = metadata.get("org", [])
    remaining = []
    deleted = None
    for item in items:
        if item.get("id") == attach_id:
            deleted = item
        else:
            remaining.append(item)

    if not deleted:
        return JsonResponse({"code": 404, "message": "附件不存在"}, status=404)

    metadata["org"] = remaining
    _save_metadata(metadata)

    # 删除文件
    public_path = deleted.get("filePath", "")
    relative = public_path.replace(settings.MEDIA_URL, "", 1)
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative)
    if os.path.exists(absolute_path):
        os.remove(absolute_path)

    return JsonResponse({"code": 200, "message": "删除成功"})


@csrf_exempt
def upload_emp_attach(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    emp_id = request.POST.get("empId")
    attach_type = request.POST.get("attachType")
    upload = request.FILES.get("file")

    if not emp_id or not attach_type or not upload:
        return JsonResponse({"success": False, "message": "empId、attachType与文件均不能为空"}, status=400)

    filename = f"{emp_id}_{attach_type}_{upload.name}"
    file_path = _build_file_path("emp_attach", filename)
    with open(file_path, "wb+") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    metadata = _load_metadata()
    attach_id = str(uuid.uuid4())
    record = {
        "id": attach_id,
        "empId": emp_id,
        "attachType": attach_type,
        "fileName": upload.name,
        "filePath": _public_path(file_path),
        "fileSize": upload.size,
        "uploadTime": timezone.now().isoformat(),
    }
    metadata.setdefault("emp", []).append(record)
    _save_metadata(metadata)

    return JsonResponse({"success": True, "data": record})


@csrf_exempt
def list_emp_attach(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "只支持GET请求"}, status=405)

    emp_id = request.GET.get("empId")
    attach_type = request.GET.get("attachType")
    if not emp_id:
        return JsonResponse({"success": False, "message": "empId不能为空"}, status=400)

    metadata = _load_metadata()
    items = [item for item in metadata.get("emp", []) if item.get("empId") == emp_id]
    if attach_type:
        items = [item for item in items if item.get("attachType") == attach_type]

    return JsonResponse({"success": True, "data": items})


@csrf_exempt
def delete_emp_attach(request, emp_attach_id):
    if request.method != "DELETE":
        return JsonResponse({"code": 405, "message": "只支持DELETE请求"}, status=405)

    metadata = _load_metadata()
    items = metadata.get("emp", [])
    remaining = []
    deleted = None
    for item in items:
        if item.get("id") == emp_attach_id:
            deleted = item
        else:
            remaining.append(item)

    if not deleted:
        return JsonResponse({"code": 404, "message": "附件不存在"}, status=404)

    metadata["emp"] = remaining
    _save_metadata(metadata)

    public_path = deleted.get("filePath", "")
    relative = public_path.replace(settings.MEDIA_URL, "", 1)
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative)
    if os.path.exists(absolute_path):
        os.remove(absolute_path)

    return JsonResponse({"code": 200, "message": "删除成功"})


@csrf_exempt
def org_attach_types(request):
    data = [
        {"code": "LICENSE", "name": "营业执照"},
        {"code": "CERT", "name": "资质证书"},
        {"code": "OTHER", "name": "其他"},
    ]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
def emp_attach_types(request):
    data = [
        {"code": "ID", "name": "身份证"},
        {"code": "HEALTH", "name": "健康证"},
        {"code": "CONTRACT", "name": "劳动合同"},
    ]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
def emp_types(request):
    data = [
        {"code": "FULLTIME", "name": "全职"},
        {"code": "PARTTIME", "name": "兼职"},
        {"code": "TEMP", "name": "临时"},
    ]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
def save_draft(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    org_id = payload.get("orgId") or str(uuid.uuid4())
    return JsonResponse({"orgId": org_id, "status": "draft"})


@csrf_exempt
def submit_review(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    org_id = payload.get("orgId") or str(uuid.uuid4())
    result = {
        "orgId": org_id,
        "status": "submitted",
        "submittedAt": datetime.utcnow().isoformat() + "Z",
        "systemRating": {
            "score": 92,
            "level": "A",
            "remarks": "自动评级完成",
        },
    }
    return JsonResponse(result)


@csrf_exempt
def full_org_info(request, org_id):
    metadata = _load_metadata()
    org_attachments = [item for item in metadata.get("org", []) if item.get("orgId") == org_id]
    employees = [
        {
            "empId": "E001",
            "name": "张三",
            "type": "FULLTIME",
            "attachments": [item for item in metadata.get("emp", []) if item.get("empId") == "E001"],
        },
        {
            "empId": "E002",
            "name": "李四",
            "type": "PARTTIME",
            "attachments": [item for item in metadata.get("emp", []) if item.get("empId") == "E002"],
        },
    ]
    data = {
        "orgId": org_id,
        "institutionInfo": {
            "orgName": "示例机构",
            "orgCode6": "123456",
            "cityId": "1001",
            "countyId": "100101",
        },
        "employees": employees,
        "orgAttachments": org_attachments,
    }
    return JsonResponse(data)


@csrf_exempt
def validate_org_info(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    errors = []
    if not payload.get("orgName"):
        errors.append("机构名称不能为空")
    if not payload.get("orgCode6"):
        errors.append("机构代码不能为空")

    return JsonResponse({"valid": len(errors) == 0, "errors": errors})


@csrf_exempt
def org_tree(request):
    data = [
        {
            "id": "1001",
            "name": "成都市",
            "children": [
                {"id": "100101", "name": "武侯区", "orgId": "ORG001"},
                {"id": "100102", "name": "锦江区", "orgId": "ORG002"},
            ],
        }
    ]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
def basic_org_info(request, org_id):
    metadata = _load_metadata()
    org_attachments = [item for item in metadata.get("org", []) if item.get("orgId") == org_id]
    data = {
        "orgId": org_id,
        "orgName": "示例机构",
        "orgCode6": "123456",
        "attachments": org_attachments,
    }
    return JsonResponse(data)


@csrf_exempt
def org_employees_preview(request, org_id):
    data = {
        "orgId": org_id,
        "statistics": {"total": 2, "fullTime": 1, "partTime": 1},
        "employees": [
            {"empId": "E001", "name": "张三", "type": "FULLTIME"},
            {"empId": "E002", "name": "李四", "type": "PARTTIME"},
        ],
    }
    return JsonResponse(data)


@csrf_exempt
def quick_create_org(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "只支持POST请求"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    org_id = str(uuid.uuid4())
    data = {"orgId": org_id, "orgName": payload.get("orgName"), "status": "created"}
    return JsonResponse(data)


@csrf_exempt
def rating_detail(request, org_id):
    data = {
        "orgId": org_id,
        "systemRating": {"score": 92, "level": "A", "factors": ["资质齐全", "员工信息完整"]},
    }
    return JsonResponse(data)


@csrf_exempt
def anomaly_detection(request, org_id):
    data = {
        "orgId": org_id,
        "anomalies": [
            {"type": "EMPLOYEE_COUNT", "message": "员工数量与上期相比增长50%"},
            {"type": "MISSING_ATTACHMENT", "message": "缺少营业执照附件"},
        ],
    }
    return JsonResponse(data)


@csrf_exempt
def audit_history(request, org_id):
    data = [
        {"time": "2024-01-01 10:00", "result": "通过", "auditor": "管理员"},
        {"time": "2023-12-15 15:30", "result": "驳回", "auditor": "管理员"},
    ]
    return JsonResponse({"orgId": org_id, "history": data})


@csrf_exempt
def org_statistics(request, org_id):
    data = {
        "orgId": org_id,
        "fullTime": 10,
        "partTime": 5,
        "temp": 2,
        "blindPercentage": 0.05,
    }
    return JsonResponse(data)
