FROM public.ecr.aws/lambda/python:3.12

# Copiar requirements desde subcarpeta "app"
COPY app/requirements.txt .

# Instalar dependencias
RUN python -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copiar el código completo de la Lambda
COPY app/ ${LAMBDA_TASK_ROOT}

# Definir el handler principal
CMD ["lambda_function.lambda_handler"]

