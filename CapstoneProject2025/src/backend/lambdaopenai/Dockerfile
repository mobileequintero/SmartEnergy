FROM public.ecr.aws/lambda/python:3.12

# Copiar dependencias
COPY requirements.txt  .
RUN python -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copiar el código principal
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Definir el handler
CMD ["lambda_function.lambda_handler"]
