FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

RUN mkdir -p /etc/nginx/certs \
  && openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/self.key \
    -out /etc/nginx/certs/self.crt \
    -subj "/CN=192.168.80.230" \
    -addext "subjectAltName=IP:192.168.80.230,IP:127.0.0.1,DNS:localhost"

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 443

