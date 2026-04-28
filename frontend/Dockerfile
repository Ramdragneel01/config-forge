FROM cgr.dev/chainguard/node:latest-dev AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend .
RUN npm run build

FROM cgr.dev/chainguard/node:latest
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/server.mjs ./server.mjs
EXPOSE 8120
CMD ["node", "server.mjs"]
