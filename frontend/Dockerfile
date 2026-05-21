# Stage 1: build React app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build


# Stage 2: serve with nginx
FROM nginx:alpine AS runtime

# Rm def nginx conf
RUN rm /etc/nginx/conf.d/default.conf

# Cfg
COPY nginx.conf /etc/nginx/conf.d/app.conf

# React-app
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
 