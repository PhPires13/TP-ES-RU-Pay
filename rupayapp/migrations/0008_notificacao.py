'''
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rupayapp', '0007_user_theme_preference'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('SALDO_BAIXO', 'Saldo Baixo'), ('RECARGA', 'Recarga Realizada')], max_length=20)),
                ('mensagem', models.TextField()),
                ('lida', models.BooleanField(default=False)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('aluno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-criada_em'],
            },
        ),
    ]
    '''