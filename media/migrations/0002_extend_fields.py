from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="medicorgattachtype",
            name="category",
            field=models.CharField(default="", max_length=64, verbose_name="分类"),
        ),
        migrations.AddField(
            model_name="medicorgattachtype",
            name="is_required",
            field=models.BooleanField(default=False, verbose_name="是否必填"),
        ),
        migrations.AddField(
            model_name="medicempattachtype",
            name="category",
            field=models.CharField(default="", max_length=64, verbose_name="分类"),
        ),
        migrations.AddField(
            model_name="medicempattachtype",
            name="is_required",
            field=models.BooleanField(default=False, verbose_name="是否必填"),
        ),
        migrations.AddField(
            model_name="medicorginfo",
            name="legal_person_disability_no",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="法人残疾证号"),
        ),
        migrations.AddField(
            model_name="medicorginfo",
            name="legal_person_id",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="法定代表人证件号"),
        ),
        migrations.AddField(
            model_name="medicorginfo",
            name="legal_person_is_blind",
            field=models.BooleanField(default=False, verbose_name="法人是否盲人"),
        ),
        migrations.AddField(
            model_name="medicorginfo",
            name="legal_person_name",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="法定代表人姓名"),
        ),
        migrations.AddField(
            model_name="medicempinfo",
            name="disability_no",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="残疾证号"),
        ),
        migrations.AddField(
            model_name="medicempinfo",
            name="is_legal_person",
            field=models.BooleanField(default=False, verbose_name="是否法人"),
        ),
        migrations.AlterField(
            model_name="medicempinfo",
            name="emp_type",
            field=models.CharField(
                choices=[("BLIND", "盲人"), ("ABLE_BODIED", "健全"), ("OTHER", "其他")],
                max_length=32,
                verbose_name="员工类型",
            ),
        ),
    ]
