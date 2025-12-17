from django.urls import path

from . import views

urlpatterns = [
    # 字典
    path("org-attach-type", views.org_attach_types),
    path("emp-attach-type", views.emp_attach_types),
    path("emp-type", views.emp_types),

    # 机构
    path("org-info", views.org_info),
    path("org-info/<int:org_id>", views.org_info),

    # 员工
    path("emp-info", views.emp_info),
    path("emp-info/batch", views.emp_batch),
    path("emp-info/<int:emp_id>", views.emp_info),

    # 附件
    path("org-attach/upload", views.org_attach),
    path("org-attach/<int:identifier>", views.org_attach),
    path("emp-attach/upload", views.emp_attach),
    path("emp-attach/<int:identifier>", views.emp_attach),

    # 草稿
    path("draft/save", views.save_draft),

    # 组织树与加载
    path("org-tree", views.org_tree),
    path("org-info/<int:org_id>/employees", views.org_employees),
    path("org-tree/institution", views.create_org_node),
]
