from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os

@csrf_exempt
def upload_emp_attach(request):
    """上传员工附件接口"""
    if request.method == 'POST':
        # 获取表单数据
        emp_id = request.POST.get('empId')
        attach_type = request.POST.get('attachType')
        
        # 获取文件
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({
                'success': False,
                'message': '文件不能为空'
            }, status=400)
        
        if not emp_id or not attach_type:
            return JsonResponse({
                'success': False,
                'message': 'empId和attachType不能为空'
            }, status=400)
        
        # 生成文件存储路径
        filename = f"{emp_id}_{attach_type}_{file.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        # 保存文件
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # 创建数据库记录
        emp_attach = EmpAttach(
            emp_id=emp_id,
            attach_type=attach_type,
            file=file,
            created_at=timezone.now()
        )
        emp_attach.save()
        
        # 返回附件信息
        return JsonResponse({
            'success': True,
            'data': {
                'empId': emp_id,
                'attachType': attach_type,
                'fileName': file.name,
                'filePath': f"/media/{filename}",
                'fileSize': file.size,
                'uploadTime': str(file.uploaded_at) if hasattr(file, 'uploaded_at') else None
            }
        })
    
    return JsonResponse({
        'success': False,
        'message': '只支持POST请求'
    }, status=405)

@csrf_exempt
def get_emp_attach_list(request):
    """获取员工附件列表接口"""
    if request.method == 'GET':
        emp_id = request.GET.get('empId')
        attach_type = request.GET.get('attachType')
        
        if not emp_id:
            return JsonResponse({
                'success': False,
                'message': 'empId不能为空'
            }, status=400)
        
        # 查询数据库中的附件记录
        if attach_type:
            attachments = EmpAttach.objects.filter(emp_id=emp_id, attach_type=attach_type)
        else:
            attachments = EmpAttach.objects.filter(emp_id=emp_id)
        
        # 构建响应数据
        attachment_list = []
        for attach in attachments:
            attachment_list.append({
                'id': attach.id,
                'empId': attach.emp_id,
                'attachType': attach.attach_type,
                'fileName': attach.file.name,
                'filePath': f"/media/{attach.file.name}",
                'fileSize': attach.file.size,
                'uploadTime': attach.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'data': attachment_list
        })
    
    return JsonResponse({
        'success': False,
        'message': '只支持GET请求'
    }, status=405)

@csrf_exempt
def delete_emp_attach(request, emp_attach_id):
    """删除员工附件接口"""
    if request.method == 'DELETE':
        try:
            emp_attach = EmpAttach.objects.get(id=emp_attach_id)
            
            # 删除文件
            file_path = os.path.join(settings.MEDIA_ROOT, emp_attach.file.name)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除数据库记录
            emp_attach.delete()
            
            return JsonResponse({
                'code': 200,
                'message': '删除成功'
            })
        except EmpAttach.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '附件不存在'
            })
    
    return JsonResponse({
        'code': 405,
        'message': '只支持DELETE请求'
    }, status=405)