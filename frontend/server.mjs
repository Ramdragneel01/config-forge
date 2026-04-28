import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.join(__dirname, "dist");
const port = Number(process.env.PORT ?? 8120);

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon"
};

const server = http.createServer((req, res) => {
  const reqPath = req.url === "/" ? "/index.html" : req.url ?? "/index.html";
  const cleanPath = reqPath.split("?")[0];
  const filePath = path.join(distDir, cleanPath);

  let resolvedPath = filePath;
  if (!fs.existsSync(resolvedPath) || fs.statSync(resolvedPath).isDirectory()) {
    resolvedPath = path.join(distDir, "index.html");
  }

  fs.readFile(resolvedPath, (err, content) => {
    if (err) {
      res.statusCode = 500;
      res.end("Server error");
      return;
    }

    const ext = path.extname(resolvedPath);
    res.setHeader("Content-Type", mimeTypes[ext] ?? "application/octet-stream");
    res.end(content);
  });
});

server.listen(port, "0.0.0.0", () => {
  console.log(`config-forge frontend listening on ${port}`);
});
