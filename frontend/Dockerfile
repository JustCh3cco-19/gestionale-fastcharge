FROM nginx:alpine

# Copia i file del frontend nella cartella di default di Nginx
COPY . /usr/share/nginx/html

# Espone la porta 80 (quella di default di Nginx)
EXPOSE 80

# Avvia Nginx in modalità "foreground"
CMD ["nginx", "-g", "daemon off;"]
