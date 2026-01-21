{{- define "syncshield.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "syncshield.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "syncshield.labels" -}}
app.kubernetes.io/name: {{ include "syncshield.name" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "syncshield.syncvalueFullname" -}}
{{- printf "%s-syncvalue" (include "syncshield.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "syncshield.syncflowFullname" -}}
{{- printf "%s-syncflow" (include "syncshield.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
