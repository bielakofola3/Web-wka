# MycoForum
FROM python:3.12-slim

WORKDIR /app

# Nie root
RUN useradd -m -u 1000 myco && chown -R myco:myco /app
USER myco

COPY --chown=myco:myco requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=myco:myco . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
