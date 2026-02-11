# 🚀 Quick Migration Guide - SEO Intelligence Platform

## Situation

Du har **100 verktyg** som alla följer samma mönster:
- Config → Service → Result
- Alla async
- Alla har initialize/close
- **100% drop-in ready**

## Migration: 4 Steg (30 min - 2 timmar)

### Steg 1: Kopiera Framework (5 min)

```bash
# Kopiera hela v2-mappen till din plattform
cp -r seo-tool-framework/v2 /path/to/your/platform/framework

# Eller bara core-filerna
cp -r seo-tool-framework/v2/core /path/to/your/platform/framework/
cp -r seo-tool-framework/v2/api /path/to/your/platform/framework/
cp seo-tool-framework/v2/frontend/index.html /path/to/your/platform/static/
```

### Steg 2: Länka Verktyg (2 min)

```bash
cd /path/to/your/platform/framework

# Skapa tools-mapp med symlinks till befintliga verktyg
mkdir -p tools
ln -s ../ml-service/app/features tools/ml_features
ln -s ../services/tier1-priority tools/tier1
ln -s ../services/tier2-core tools/tier2
ln -s ../ml-service/app/features_advanced tools/advanced
```

### Steg 3: Generera Manifests (10 min)

```bash
# Använd din COMBINED_ANALYSIS.json från skanningen
python scripts/generate_manifests.py \
    --analysis /path/to/_tool_analysis/COMBINED_ANALYSIS.json \
    --output manifests/

# Resultat: 55 YAML-manifests (dubbletter bortrensade)
```

### Steg 4: Starta (1 min)

```bash
pip install -r requirements.txt
python -m uvicorn api.server:app --reload --port 8000

# Öppna http://localhost:8000
```

---

## Vad Du Får

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  🧠 SEO Intelligence Platform                                │
│  ─────────────────────────────────────────                  │
│                                                              │
│  [🔍 Analyzers]  [✨ Generators]  [📊 Monitors]  [⚡ Optimizers]
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Content Gap     │  │ Keyword         │  │ SERP        │  │
│  │ Discovery 🎯    │  │ Clustering 🔍   │  │ Monitor 📊  │  │
│  │                 │  │                 │  │             │  │
│  │ [Execute]       │  │ [Execute]       │  │ [Execute]   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                              │
│  ... +97 fler verktyg                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Anpassa Manifests

De auto-genererade manifesten har placeholder-inputs. Förbättra dem:

### Före (auto-genererad):
```yaml
inputs:
  - name: data
    label: "Input Data"
    type: textarea
```

### Efter (anpassad):
```yaml
inputs:
  - name: domain
    label: "Your Domain"
    type: text
    required: true
    placeholder: "example.com"
  
  - name: competitors
    label: "Competitors"
    type: url_list
    placeholder: "competitor1.com\ncompetitor2.com"
```

---

## Integrera med NestJS Backend

Framework:et körs standalone, men kan integreras:

### Option A: Proxy via NestJS

```typescript
// nest-backend/src/tools/tools.controller.ts
@Controller('api/tools')
export class ToolsController {
  
  @Post(':id/execute')
  async execute(@Param('id') id: string, @Body() data: any) {
    // Proxy to Python framework
    const response = await fetch(`http://localhost:8000/api/tools/${id}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    });
    return response.json();
  }
}
```

### Option B: Shared API Gateway

```yaml
# nginx.conf
location /api/tools {
    proxy_pass http://python-framework:8000;
}

location /api {
    proxy_pass http://nestjs-backend:3000;
}
```

---

## Nästa Steg

1. ✅ **Idag**: Kör migration, se alla 100 verktyg i UI
2. 📝 **Nästa dag**: Anpassa 10 viktigaste manifests
3. 🔗 **Vecka 1**: Integrera med NestJS backend
4. 🎨 **Vecka 2**: Anpassa frontend-design
5. 🚀 **Vecka 3**: Deploy till staging

---

## Support

Har du problem? Vanliga issues:

### Import Error
```
ModuleNotFoundError: No module named 'ml_features'
```
**Fix:** Kontrollera symlinks och PYTHONPATH

### Async Error
```
RuntimeWarning: coroutine 'X' was never awaited
```
**Fix:** Alla tools är async - kontrollera att manifestet pekar på rätt metod

### YAML Parse Error
```
yaml.scanner.ScannerError
```
**Fix:** Validera YAML syntax (inga tabs, rätt indentation)

---

*Framework byggt för 100% drop-in compatibility med din befintliga kodbas!*
