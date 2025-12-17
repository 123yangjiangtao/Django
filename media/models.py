from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")

    class Meta:
        abstract = True


class MedicOrgAttachType(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=128, verbose_name="附件类型名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="附件类型编码")
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="描述")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "medic_org_attach_type"
        verbose_name = "机构附件类型"
        verbose_name_plural = "机构附件类型"

    def __str__(self):
        return f"{self.code}-{self.name}"


class MedicEmpAttachType(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=128, verbose_name="附件类型名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="附件类型编码")
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="描述")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "medic_emp_attach_type"
        verbose_name = "员工附件类型"
        verbose_name_plural = "员工附件类型"

    def __str__(self):
        return f"{self.code}-{self.name}"


class MedicOrgInfo(TimeStampedModel, SoftDeleteModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "草稿"),
        (STATUS_SUBMITTED, "已提交"),
        (STATUS_APPROVED, "通过"),
        (STATUS_REJECTED, "退回"),
    )

    org_name = models.CharField(max_length=255, verbose_name="机构名称")
    org_code6 = models.CharField(max_length=64, verbose_name="机构代码")
    city_id = models.CharField(max_length=64, blank=True, default="", verbose_name="城市ID")
    county_id = models.CharField(max_length=64, blank=True, default="", verbose_name="区县ID")
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="父节点"
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="状态")

    class Meta:
        db_table = "medic_org_info"
        verbose_name = "机构信息"
        verbose_name_plural = "机构信息"

    def __str__(self):
        return self.org_name


class MedicEmpInfo(TimeStampedModel, SoftDeleteModel):
    TYPE_BLIND = "BLIND"
    TYPE_HEALTHY = "HEALTHY"
    TYPE_OTHER = "OTHER"
    EMP_TYPE_CHOICES = (
        (TYPE_BLIND, "盲人"),
        (TYPE_HEALTHY, "健全"),
        (TYPE_OTHER, "其他"),
    )

    org = models.ForeignKey(MedicOrgInfo, related_name="employees", on_delete=models.CASCADE, verbose_name="机构")
    emp_name = models.CharField(max_length=255, verbose_name="员工姓名")
    emp_type = models.CharField(max_length=32, choices=EMP_TYPE_CHOICES, verbose_name="员工类型")
    id_number = models.CharField(max_length=64, verbose_name="证件号")
    phone = models.CharField(max_length=32, blank=True, default="", verbose_name="联系电话")

    class Meta:
        db_table = "medic_emp_info"
        verbose_name = "员工信息"
        verbose_name_plural = "员工信息"

    def __str__(self):
        return self.emp_name


class MedicOrgAttach(TimeStampedModel, SoftDeleteModel):
    org = models.ForeignKey(MedicOrgInfo, related_name="attachments", on_delete=models.CASCADE, verbose_name="机构")
    attach_type = models.ForeignKey(
        MedicOrgAttachType, related_name="attachments", on_delete=models.PROTECT, verbose_name="附件类型"
    )
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_path = models.CharField(max_length=255, verbose_name="文件路径")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小")

    class Meta:
        db_table = "medic_org_attach"
        verbose_name = "机构附件"
        verbose_name_plural = "机构附件"

    def __str__(self):
        return self.file_name


class MedicEmpAttach(TimeStampedModel, SoftDeleteModel):
    emp = models.ForeignKey(MedicEmpInfo, related_name="attachments", on_delete=models.CASCADE, verbose_name="员工")
    attach_type = models.ForeignKey(
        MedicEmpAttachType, related_name="attachments", on_delete=models.PROTECT, verbose_name="附件类型"
    )
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_path = models.CharField(max_length=255, verbose_name="文件路径")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小")

    class Meta:
        db_table = "medic_emp_attach"
        verbose_name = "员工附件"
        verbose_name_plural = "员工附件"

    def __str__(self):
        return self.file_name


class BaseApply(TimeStampedModel):
    org = models.ForeignKey(MedicOrgInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="机构")
    emp = models.ForeignKey(MedicEmpInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="员工")
    payload = models.JSONField(default=dict, verbose_name="数据快照")
    status = models.CharField(max_length=32, default=MedicOrgInfo.STATUS_DRAFT, verbose_name="状态")

    class Meta:
        abstract = True


class MedicApplyApprove(BaseApply):
    class Meta:
        db_table = "medic_apply_approve"
        verbose_name = "审批记录"
        verbose_name_plural = "审批记录"


class MedicApplyAudit(BaseApply):
    class Meta:
        db_table = "medic_apply_audit"
        verbose_name = "审核记录"
        verbose_name_plural = "审核记录"


class MedicApplyReject(BaseApply):
    reason = models.CharField(max_length=255, blank=True, default="", verbose_name="退回原因")

    class Meta:
        db_table = "medic_apply_reject"
        verbose_name = "退回记录"
        verbose_name_plural = "退回记录"
