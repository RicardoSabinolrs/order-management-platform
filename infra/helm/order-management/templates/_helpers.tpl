{{/* Nome base do chart. */}}
{{- define "order-management.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Nome completo dos recursos. */}}
{{- define "order-management.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "order-management.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "order-management.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "order-management.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: order-management
{{- end -}}

{{- define "order-management.selectorLabels" -}}
app.kubernetes.io/name: {{ include "order-management.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Tag da imagem: exigida explicitamente, para que o deploy seja reproduzivel. */}}
{{- define "order-management.imageTag" -}}
{{- if .Values.image.tag -}}
{{- .Values.image.tag -}}
{{- else -}}
{{- fail "image.tag e obrigatorio: o pipeline deve injetar o digest/sha do commit." -}}
{{- end -}}
{{- end -}}

{{/* Registry vazio significa imagem local (minikube), sem prefixo de registro. */}}
{{- define "order-management.imagePrefix" -}}
{{- if .Values.image.registry -}}{{ .Values.image.registry }}/{{- end -}}
{{- end -}}

{{- define "order-management.apiImage" -}}
{{ include "order-management.imagePrefix" . }}{{ .Values.image.repository }}-api:{{ include "order-management.imageTag" . }}
{{- end -}}

{{- define "order-management.webImage" -}}
{{ include "order-management.imagePrefix" . }}{{ .Values.image.repository }}-web:{{ include "order-management.imageTag" . }}
{{- end -}}

{{/* Variaveis de conexao com o banco, compartilhadas pela API e pelo job de migration. */}}
{{- define "order-management.databaseEnv" -}}
- name: POSTGRES_HOST
  value: {{ .Values.database.host | quote }}
- name: POSTGRES_PORT
  value: {{ .Values.database.port | quote }}
- name: POSTGRES_DB
  value: {{ .Values.database.name | quote }}
- name: POSTGRES_USER
  value: {{ .Values.database.user | quote }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.database.existingSecret | quote }}
      key: {{ .Values.database.existingSecretPasswordKey | quote }}
{{- end -}}
