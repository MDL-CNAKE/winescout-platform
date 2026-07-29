# Stage 1: build - compila il codice React/TypeScript in file statici.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# VITE_API_URL viene "bruciato" nel bundle statico a build-time: in
# produzione il backend deve essere raggiungibile a questo indirizzo dal
# browser dell'utente, non dal container (per questo NON usiamo "backend"
# come nome host qui, a differenza delle variabili lato server).
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Stage 2: serve - nginx serve solo i file statici generati, immagine
# finale molto più piccola (non contiene node_modules).
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
