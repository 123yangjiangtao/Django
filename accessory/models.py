from django.db import models

class OrgAttach(models.Model):
    org_id = models.CharField(max_length=100, verbose_name='机构ID')
    attach_type = models.CharField(max_length=50, verbose_name='附件类型')
    file = models.FileField(upload_to='org_attach/', verbose_name='附件文件')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'org_attach'
        verbose_name = '机构附件'
        verbose_name_plural = '机构附件'

    def __str__(self):
        return f"{self.org_id}_{self.attach_type}"

class EmpAttach(models.Model):
    emp_id = models.CharField(max_length=100, verbose_name='员工ID')
    attach_type = models.CharField(max_length=50, verbose_name='附件类型')
    file = models.FileField(upload_to='emp_attach/', verbose_name='附件文件')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'emp_attach'
        verbose_name = '员工附件'
        verbose_name_plural = '员工附件'

    def __str__(self):
        return f"{self.emp_id}_{self.attach_type}"