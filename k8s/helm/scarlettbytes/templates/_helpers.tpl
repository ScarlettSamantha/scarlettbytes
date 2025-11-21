{{- define "scarlettbytes.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "scarlettbytes.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "scarlettbytes.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}
{{- end }}

{{- define "scarlettbytes.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "scarlettbytes.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "scarlettbytes.selectorLabels.web" -}}
app.kubernetes.io/name: {{ include "scarlettbytes.name" . }}-web
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "scarlettbytes.selectorLabels.memcached" -}}
app.kubernetes.io/name: {{ include "scarlettbytes.name" . }}-memcached
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
