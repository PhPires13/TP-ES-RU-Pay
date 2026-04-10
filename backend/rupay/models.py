from django.db import models

class Aluno(models.Model):
  primeiroNome = models.CharField(max_length=30)
  sobrenome = models.CharField(max_length=30)
  matricula = models.CharField(max_length=20, unique=True)
  saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Funcionario(models.Model):
  primeiroNome = models.CharField(max_length=30)
  sobrenome = models.CharField(max_length=30)
  matricula = models.CharField(max_length=20, unique=True)