# Build ASan/UBSan del backend SDL (T-618, Paso 1). Imagen oficial gcc fijada por digest:
# docker.io/library/gcc:13-bookworm (Debian bookworm), con libsdl2-dev de bookworm (2.26.5).
FROM gcc@sha256:20eec427045c47d0aad1bd28c81d435916c327cd992240aa78350f755d04d04a
RUN apt-get update && apt-get install -y --no-install-recommends libsdl2-dev && rm -rf /var/lib/apt/lists/*
