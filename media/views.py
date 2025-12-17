import json
import os
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import (
    MedicApplyAudit,
    MedicEmpAttach,
    MedicEmpAttachType,
    MedicEmpInfo,
    MedicOrgAttach,
    MedicOrgAttachType,
    MedicOrgInfo,
)


MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "doc", "docx"}
storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)

DEFAULT_ORG_ATTACH_TYPES = [
    {"code": "BUSINESS_LICENSE", "name": "营业执照", "category": "基本信息", "is_required": True},
    {"code": "PRACTICE_PERMIT", "name": "医疗执业许可证", "category": "资质", "is_required": True},
    {"code": "TAX_REG", "name": "税务登记", "category": "资质", "is_required": False},
    {"code": "BANK_ACCOUNT", "name": "开户许可证", "category": "资质", "is_required": False},
    {"code": "LEGAL_ID", "name": "法人身份证", "category": "法人", "is_required": True},
    {"code": "SITE_CONTRACT", "name": "场地租赁合同", "category": "场地", "is_required": False},
    {"code": "HYGIENE_PERMIT", "name": "卫生许可证", "category": "资质", "is_required": False},
    {"code": "OTHER", "name": "其他", "category": "其他", "is_required": False},
]

DEFAULT_EMP_ATTACH_TYPES = [
    {"code": "ID_CARD", "name": "身份证", "category": "身份", "is_required": True},
    {"code": "HEALTH_CERT", "name": "健康证", "category": "健康", "is_required": False},
    {"code": "CONTRACT", "name": "劳动合同", "category": "合同", "is_required": False},
    {"code": "QUALIFICATION", "name": "职业资格证", "category": "资质", "is_required": False},
    {"code": "PHOTO", "name": "个人照片", "category": "档案", "is_required": False},
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _success(data=None, message="success", status=200):
    return JsonResponse({"success": True, "message": message, "data": data}, status=status)


def _error(message, status=400, data=None):
    return JsonResponse({"success": False, "message": message, "data": data}, status=status)


def _ensure_attach_types():
    for idx, item in enumerate(DEFAULT_ORG_ATTACH_TYPES):
        obj, _ = MedicOrgAttachType.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "category": item.get("category", ""),
                "is_required": item.get("is_required", False),
                "sort_order": idx,
            },
        )
        if obj.name != item["name"] or obj.category != item.get("category", "") or obj.is_required != item.get("is_required", False):
            obj.name = item["name"]
            obj.category = item.get("category", "")
            obj.is_required = item.get("is_required", False)
            obj.sort_order = idx
            obj.save()
    for idx, item in enumerate(DEFAULT_EMP_ATTACH_TYPES):
        obj, _ = MedicEmpAttachType.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "category": item.get("category", ""),
                "is_required": item.get("is_required", False),
                "sort_order": idx,
            },
        )
        if obj.name != item["name"] or obj.category != item.get("category", "") or obj.is_required != item.get("is_required", False):
            obj.name = item["name"]
            obj.category = item.get("category", "")
            obj.is_required = item.get("is_required", False)
            obj.sort_order = idx
            obj.save()


def _serialize_org(org: MedicOrgInfo):
    return {
        "orgId": org.id,
        "orgName": org.org_name,
        "orgCode6": org.org_code6,
        "cityId": org.city_id,
        "countyId": org.county_id,
        "legalPersonName": org.legal_person_name,
        "legalPersonId": org.legal_person_id,
        "legalPersonIsBlind": org.legal_person_is_blind,
        "legalPersonDisabilityNo": org.legal_person_disability_no,
        "parentId": org.parent_id,
        "status": org.status,
        "createdAt": org.created_at,
        "updatedAt": org.updated_at,
    }


def _serialize_emp(emp: MedicEmpInfo):
    return {
        "empId": emp.id,
        "orgId": emp.org_id,
        "empName": emp.emp_name,
        "empType": emp.emp_type,
        "idNumber": emp.id_number,
        "phone": emp.phone,
        "isLegalPerson": emp.is_legal_person,
        "disabilityNo": emp.disability_no,
        "createdAt": emp.created_at,
        "updatedAt": emp.updated_at,
    }


def _serialize_attachment(record):
    return {
        "id": record.id,
        "orgId": getattr(record, "org_id", None),
        "empId": getattr(record, "emp_id", None),
        "attachType": record.attach_type.code,
        "attachTypeName": record.attach_type.name,
        "fileName": record.file_name,
        "filePath": record.file_path,
        "fileSize": record.file_size,
        "createdAt": record.created_at,
    }


def _validate_org_payload(payload, partial=False):
    required = ["orgName", "orgCode6", "cityId", "countyId"]
    if not partial:
        missing = [field for field in required if not payload.get(field)]
        if missing:
            return False, f"{'、'.join(missing)} 为必填项"
    if payload.get("legalPersonIsBlind") and not payload.get("legalPersonDisabilityNo"):
        return False, "法人盲人时需填写残疾证号"
    return True, ""


def _validate_emp_payload(payload, partial=False):
    base_required = ["empName", "idNumber", "empType", "orgId"]
    if not partial:
        missing = [field for field in base_required if not payload.get(field)]
        if missing:
            return False, f"{'、'.join(missing)} 为必填项"
    if payload.get("empType") == MedicEmpInfo.TYPE_BLIND and not payload.get("disabilityNo"):
        return False, "盲人员工需填写残疾证号"
    return True, ""


# ---------------------------------------------------------------------------
# 字典类接口
# ---------------------------------------------------------------------------


@csrf_exempt
def org_attach_types(request):
    _ensure_attach_types()
    types = (
        MedicOrgAttachType.objects.filter(is_delete=False).order_by("sort_order", "id")
    )
    data = [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "category": item.category,
            "isRequired": item.is_required,
            "description": item.description,
        }
        for item in types
    ]
    return _success(data)


@csrf_exempt
def emp_attach_types(request):
    _ensure_attach_types()
    types = (
        MedicEmpAttachType.objects.filter(is_delete=False).order_by("sort_order", "id")
    )
    data = [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "category": item.category,
            "isRequired": item.is_required,
            "description": item.description,
        }
        for item in types
    ]
    return _success(data)


@csrf_exempt
def emp_types(request):
    data = [
        {"code": MedicEmpInfo.TYPE_BLIND, "name": "盲人"},
        {"code": MedicEmpInfo.TYPE_ABLE, "name": "健全"},
        {"code": MedicEmpInfo.TYPE_OTHER, "name": "其他"},
    ]
    return _success(data)


# ---------------------------------------------------------------------------
# 机构信息
# ---------------------------------------------------------------------------


@csrf_exempt
def org_info(request, org_id=None):
    if request.method == "POST":
        payload = _json_body(request)
        ok, msg = _validate_org_payload(payload)
        if not ok:
            return _error(msg, status=400)
        org = MedicOrgInfo.objects.create(
            org_name=payload.get("orgName", ""),
            org_code6=payload.get("orgCode6", ""),
            city_id=payload.get("cityId", ""),
            county_id=payload.get("countyId", ""),
            legal_person_name=payload.get("legalPersonName", ""),
            legal_person_id=payload.get("legalPersonId", ""),
            legal_person_is_blind=bool(payload.get("legalPersonIsBlind")),
            legal_person_disability_no=payload.get("legalPersonDisabilityNo", ""),
            parent_id=payload.get("parentId"),
            status=MedicOrgInfo.STATUS_DRAFT,
        )
        return _success(_serialize_org(org), "创建成功")

    if not org_id:
        return _error("orgId不能为空", status=400)

    try:
        org = MedicOrgInfo.objects.get(pk=org_id, is_delete=False)
    except MedicOrgInfo.DoesNotExist:
        return _error("机构不存在", status=404)

    if request.method == "PUT":
        if org.status not in {MedicOrgInfo.STATUS_DRAFT, MedicOrgInfo.STATUS_REJECTED}:
            return _error("仅草稿或退回状态允许修改", status=400)
        payload = _json_body(request)
        ok, msg = _validate_org_payload(payload, partial=True)
        if not ok:
            return _error(msg, status=400)
        org.org_name = payload.get("orgName", org.org_name)
        org.org_code6 = payload.get("orgCode6", org.org_code6)
        org.city_id = payload.get("cityId", org.city_id)
        org.county_id = payload.get("countyId", org.county_id)
        org.legal_person_name = payload.get("legalPersonName", org.legal_person_name)
        org.legal_person_id = payload.get("legalPersonId", org.legal_person_id)
        org.legal_person_is_blind = payload.get("legalPersonIsBlind", org.legal_person_is_blind)
        org.legal_person_disability_no = payload.get("legalPersonDisabilityNo", org.legal_person_disability_no)
        org.parent_id = payload.get("parentId", org.parent_id)
        org.save()
        return _success(_serialize_org(org), "更新成功")

    if request.method == "DELETE":
        org.is_delete = True
        org.save(update_fields=["is_delete", "updated_at"])
        return _success(message="删除成功")

    if request.method == "GET":
        attachments = [
            _serialize_attachment(item)
            for item in org.attachments.filter(is_delete=False).select_related("attach_type")
        ]
        data = _serialize_org(org)
        data["attachments"] = attachments
        latest_audit = MedicApplyAudit.objects.filter(org=org).order_by("-created_at").first()
        data["auditStatus"] = latest_audit.status if latest_audit else org.status
        data["status"] = org.status
        return _success(data)

    return _error("不支持的请求方法", status=405)


# ---------------------------------------------------------------------------
# 员工信息
# ---------------------------------------------------------------------------


@csrf_exempt
def emp_info(request, emp_id=None):
    if request.method == "POST":
        payload = _json_body(request)
        ok, msg = _validate_emp_payload(payload)
        if not ok:
            return _error(msg, status=400)
        org_id = payload.get("orgId")
        emp_type = payload.get("empType")
        id_number = payload.get("idNumber")
        is_legal_person = bool(payload.get("isLegalPerson"))
        try:
            org = MedicOrgInfo.objects.get(pk=org_id, is_delete=False)
        except MedicOrgInfo.DoesNotExist:
            return _error("机构不存在", status=404)
        duplicate = MedicEmpInfo.objects.filter(
            id_number=id_number, is_delete=False
        ).exclude(org_id=org_id)
        if duplicate.exists() and not (is_legal_person and emp_type == MedicEmpInfo.TYPE_BLIND):
            return _error("存在跨机构挂靠的员工记录", status=400)
        emp = MedicEmpInfo.objects.create(
            org=org,
            emp_name=payload.get("empName", ""),
            emp_type=emp_type,
            id_number=id_number,
            phone=payload.get("phone", ""),
            is_legal_person=is_legal_person,
            disability_no=payload.get("disabilityNo", ""),
        )
        return _success(_serialize_emp(emp), "创建成功")

    if not emp_id:
        return _error("empId不能为空", status=400)

    try:
        emp = MedicEmpInfo.objects.select_related("org").get(pk=emp_id, is_delete=False)
    except MedicEmpInfo.DoesNotExist:
        return _error("员工不存在", status=404)

    if request.method == "PUT":
        payload = _json_body(request)
        ok, msg = _validate_emp_payload(payload, partial=True)
        if not ok:
            return _error(msg, status=400)
        new_org_id = payload.get("orgId", emp.org_id)
        id_number = payload.get("idNumber", emp.id_number)
        if not id_number:
            return _error("idNumber 不能为空", status=400)
        is_legal_person = payload.get("isLegalPerson", emp.is_legal_person)
        emp_type = payload.get("empType", emp.emp_type)
        duplicate = (
            MedicEmpInfo.objects.filter(id_number=id_number, is_delete=False)
            .exclude(pk=emp_id)
            .exclude(org_id=new_org_id)
        )
        if duplicate.exists() and not (is_legal_person and emp_type == MedicEmpInfo.TYPE_BLIND):
            return _error("存在跨机构挂靠的员工记录", status=400)
        if new_org_id != emp.org_id:
            try:
                emp.org = MedicOrgInfo.objects.get(pk=new_org_id, is_delete=False)
            except MedicOrgInfo.DoesNotExist:
                return _error("目标机构不存在", status=404)
        emp.emp_name = payload.get("empName", emp.emp_name)
        emp.emp_type = emp_type
        emp.id_number = id_number
        emp.phone = payload.get("phone", emp.phone)
        emp.is_legal_person = is_legal_person
        emp.disability_no = payload.get("disabilityNo", emp.disability_no)
        emp.save()
        return _success(_serialize_emp(emp), "更新成功")

    if request.method == "DELETE":
        emp.is_delete = True
        emp.save(update_fields=["is_delete", "updated_at"])
        return _success(message="删除成功")

    if request.method == "GET":
        attachments = [
            _serialize_attachment(item)
            for item in emp.attachments.filter(is_delete=False).select_related("attach_type")
        ]
        data = _serialize_emp(emp)
        data["attachments"] = attachments
        return _success(data)

    return _error("不支持的请求方法", status=405)


@csrf_exempt
def emp_batch(request):
    if request.method != "POST":
        return _error("只支持POST请求", status=405)
    payload = _json_body(request)
    employees = payload.get("employees", [])
    if not isinstance(employees, list):
        return _error("employees 必须为数组", status=400)

    results = []
    for item in employees:
        org_id = item.get("orgId")
        id_number = item.get("idNumber")
        ok, msg = _validate_emp_payload(
            {
                "orgId": org_id,
                "empName": item.get("empName"),
                "idNumber": id_number,
                "empType": item.get("empType"),
                "disabilityNo": item.get("disabilityNo"),
            },
            partial=False,
        )
        if not ok:
            results.append({"orgId": org_id, "empName": item.get("empName"), "success": False, "message": msg})
            continue
        try:
            org = MedicOrgInfo.objects.get(pk=org_id, is_delete=False)
        except MedicOrgInfo.DoesNotExist:
            results.append({"orgId": org_id, "empName": item.get("empName"), "success": False, "message": "机构不存在"})
            continue
        is_legal_person = bool(item.get("isLegalPerson"))
        emp_type = item.get("empType", MedicEmpInfo.TYPE_OTHER)
        duplicate = (
            MedicEmpInfo.objects.filter(id_number=id_number, is_delete=False)
            .exclude(org_id=org_id)
            .exists()
        )
        if duplicate and not (is_legal_person and emp_type == MedicEmpInfo.TYPE_BLIND):
            results.append({"orgId": org_id, "empName": item.get("empName"), "success": False, "message": "存在跨机构挂靠记录"})
            continue
        emp = MedicEmpInfo.objects.create(
            org=org,
            emp_name=item.get("empName", ""),
            emp_type=emp_type,
            id_number=id_number,
            phone=item.get("phone", ""),
            is_legal_person=is_legal_person,
            disability_no=item.get("disabilityNo", ""),
        )
        results.append({"empId": emp.id, "orgId": org_id, "empName": emp.emp_name, "success": True})

    return _success(results, "批量创建完成")


# ---------------------------------------------------------------------------
# 附件上传/查询
# ---------------------------------------------------------------------------


def _handle_upload(upload_file, prefix):
    if not upload_file:
        return None, "文件不能为空"
    if upload_file.size > MAX_UPLOAD_SIZE:
        return None, "文件大小不能超过10MB"
    ext = upload_file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, "文件格式不支持，仅支持 jpg/jpeg/png/pdf/doc/docx"
    filename = f"{prefix}_{uuid.uuid4()}_{upload_file.name}"
    saved_path = storage.save(os.path.join(prefix, filename), upload_file)
    return saved_path, None


@csrf_exempt
def org_attach(request, identifier=None):
    if request.method == "POST":
        _ensure_attach_types()
        org_id = request.POST.get("orgId")
        attach_type_code = request.POST.get("attachType")
        upload = request.FILES.get("file")
        if not org_id or not attach_type_code:
            return _error("orgId 与 attachType 不能为空", status=400)
        try:
            org = MedicOrgInfo.objects.get(pk=org_id, is_delete=False)
            attach_type = MedicOrgAttachType.objects.get(code=attach_type_code, is_delete=False)
        except ObjectDoesNotExist:
            return _error("机构或附件类型不存在", status=404)
        saved_path, err = _handle_upload(upload, "org_attach")
        if err:
            return _error(err, status=400)
        record = MedicOrgAttach.objects.create(
            org=org,
            attach_type=attach_type,
            file_name=upload.name,
            file_path=storage.url(saved_path),
            file_size=upload.size,
        )
        return _success(_serialize_attachment(record), "上传成功")

    if request.method == "GET":
        if identifier is None:
            return _error("orgId不能为空", status=400)
        org_id = identifier
        attachments = (
            MedicOrgAttach.objects.filter(org_id=org_id, is_delete=False)
            .select_related("attach_type")
            .order_by("-created_at")
        )
        data = [_serialize_attachment(item) for item in attachments]
        return _success(data)

    if request.method == "DELETE":
        if identifier is None:
            return _error("attachId不能为空", status=400)
        attach_id = identifier
        try:
            record = MedicOrgAttach.objects.select_related("attach_type").get(pk=attach_id, is_delete=False)
        except MedicOrgAttach.DoesNotExist:
            return _error("附件不存在", status=404)
        record.is_delete = True
        record.save(update_fields=["is_delete", "updated_at"])
        # 删除文件
        if record.file_path:
            relative_path = record.file_path.replace(settings.MEDIA_URL, "", 1)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        return _success(message="删除成功")

    return _error("不支持的请求方法", status=405)


@csrf_exempt
def emp_attach(request, identifier=None):
    if request.method == "POST":
        _ensure_attach_types()
        emp_id = request.POST.get("empId")
        attach_type_code = request.POST.get("attachType")
        upload = request.FILES.get("file")
        if not emp_id or not attach_type_code:
            return _error("empId 与 attachType 不能为空", status=400)
        try:
            emp = MedicEmpInfo.objects.get(pk=emp_id, is_delete=False)
            attach_type = MedicEmpAttachType.objects.get(code=attach_type_code, is_delete=False)
        except ObjectDoesNotExist:
            return _error("员工或附件类型不存在", status=404)
        saved_path, err = _handle_upload(upload, "emp_attach")
        if err:
            return _error(err, status=400)
        record = MedicEmpAttach.objects.create(
            emp=emp,
            attach_type=attach_type,
            file_name=upload.name,
            file_path=storage.url(saved_path),
            file_size=upload.size,
        )
        return _success(_serialize_attachment(record), "上传成功")

    if request.method == "GET":
        if identifier is None:
            return _error("empId不能为空", status=400)
        emp_id = identifier
        attachments = (
            MedicEmpAttach.objects.filter(emp_id=emp_id, is_delete=False)
            .select_related("attach_type")
            .order_by("-created_at")
        )
        data = [_serialize_attachment(item) for item in attachments]
        return _success(data)

    if request.method == "DELETE":
        if identifier is None:
            return _error("attachId不能为空", status=400)
        attach_id = identifier
        try:
            record = MedicEmpAttach.objects.select_related("attach_type").get(pk=attach_id, is_delete=False)
        except MedicEmpAttach.DoesNotExist:
            return _error("附件不存在", status=404)
        record.is_delete = True
        record.save(update_fields=["is_delete", "updated_at"])
        if record.file_path:
            relative_path = record.file_path.replace(settings.MEDIA_URL, "", 1)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        return _success(message="删除成功")

    return _error("不支持的请求方法", status=405)


# ---------------------------------------------------------------------------
# 草稿
# ---------------------------------------------------------------------------


@csrf_exempt
def save_draft(request):
    if request.method != "POST":
        return _error("只支持POST请求", status=405)
    payload = _json_body(request)
    org_id = payload.get("orgId")
    org = None
    if org_id:
        org, _ = MedicOrgInfo.objects.get_or_create(
            pk=org_id,
            defaults={
                "org_name": payload.get("orgName", ""),
                "org_code6": payload.get("orgCode6", ""),
                "city_id": payload.get("cityId", ""),
                "county_id": payload.get("countyId", ""),
            },
        )
    draft = MedicApplyAudit.objects.create(org=org, payload=payload, status=MedicOrgInfo.STATUS_DRAFT)
    return _success({"draftId": draft.id, "orgId": org.id if org else None}, "草稿已保存")


# ---------------------------------------------------------------------------
# 组织树/查询
# ---------------------------------------------------------------------------


def _build_tree(nodes):
    id_map = {node["orgId"]: node for node in nodes}
    roots = []
    for node in nodes:
        parent_id = node.get("parentId")
        if parent_id and parent_id in id_map:
            id_map[parent_id].setdefault("children", []).append(node)
        else:
            roots.append(node)
    return roots


@csrf_exempt
def org_tree(request):
    qs = MedicOrgInfo.objects.filter(is_delete=False)
    city_id = request.GET.get("cityId")
    county_id = request.GET.get("countyId")
    org_code6 = request.GET.get("orgCode6")
    if not any([city_id, county_id, org_code6]):
        return _error("cityId、countyId、orgCode6 至少提供一个以限定范围", status=400)
    if city_id:
        qs = qs.filter(city_id=city_id)
    if county_id:
        qs = qs.filter(county_id=county_id)
    if org_code6:
        qs = qs.filter(org_code6=org_code6)
    orgs = qs.order_by("city_id", "county_id", "id")
    nodes = []
    for org in orgs:
        emp_count = org.employees.filter(is_delete=False).count()
        blind_count = org.employees.filter(is_delete=False, emp_type=MedicEmpInfo.TYPE_BLIND).count()
        pending_audit = MedicApplyAudit.objects.filter(org=org, status=MedicOrgInfo.STATUS_SUBMITTED).count()
        total_audit = MedicApplyAudit.objects.filter(org=org).count()
        node = _serialize_org(org)
        node.update(
            {
                "employeeCount": emp_count,
                "blindCount": blind_count,
                "blindRatio": round(blind_count / emp_count, 2) if emp_count else 0,
                "pendingAudit": pending_audit,
                "auditTotal": total_audit,
                "summary": f"[{pending_audit}/{total_audit}]",
            }
        )
        nodes.append(node)
    tree = _build_tree(nodes)
    return _success(tree)


@csrf_exempt
def org_employees(request, org_id):
    try:
        org = MedicOrgInfo.objects.get(pk=org_id, is_delete=False)
    except MedicOrgInfo.DoesNotExist:
        return _error("机构不存在", status=404)
    employees = org.employees.filter(is_delete=False)
    data = [_serialize_emp(emp) for emp in employees]
    total = employees.count()
    blind_count = employees.filter(emp_type=MedicEmpInfo.TYPE_BLIND).count()
    able_count = employees.filter(emp_type=MedicEmpInfo.TYPE_ABLE).count()
    other_count = employees.filter(emp_type=MedicEmpInfo.TYPE_OTHER).count()
    statistics = {
        "total": total,
        "blind": blind_count,
        "ableBodied": able_count,
        "other": other_count,
        "ratio": round(blind_count / total, 2) if total else 0,
    }
    return _success({"employees": data, "statistics": statistics})


# ---------------------------------------------------------------------------
# 组织树节点操作
# ---------------------------------------------------------------------------


@csrf_exempt
def create_org_node(request):
    if request.method != "POST":
        return _error("只支持POST请求", status=405)
    payload = _json_body(request)
    name = payload.get("orgName", "")
    parent_id = payload.get("parentId")
    if not name:
        return _error("orgName 为必填项", status=400)
    duplicate = MedicOrgInfo.objects.filter(org_name=name, parent_id=parent_id, is_delete=False).exists()
    if duplicate:
        return _error("同一层级下机构名称不可重复", status=400)
    org = MedicOrgInfo.objects.create(
        org_name=name,
        org_code6=payload.get("orgCode6", ""),
        city_id=payload.get("cityId", ""),
        county_id=payload.get("countyId", ""),
        parent_id=parent_id,
        status=MedicOrgInfo.STATUS_DRAFT,
    )
    return _success(_serialize_org(org), "机构节点已创建")
