# ---- DOCKERFILE (AWS Lambda compatible) ----
FROM public.ecr.aws/lambda/python:3.12

# Copy app code and dependencies
COPY requirements.txt  .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY app.py ${LAMBDA_TASK_ROOT}

# Command to run your handler
CMD ["app.lambda_handler"]
