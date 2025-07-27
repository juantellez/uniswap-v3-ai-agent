# 🦄 Uniswap V3 Portfolio AI Agent

![Uniswap V3](https://img.shields.io/badge/Uniswap-V3-FF007A?style=for-the-badge&logo=uniswap)
![n8n](https://img.shields.io/badge/n8n-Workflow-EA4B71?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **Agente de IA avanzado para monitoreo automático de posiciones de liquidez en Uniswap V3**

Monitorea tus posiciones LP 24/7, calcula pérdida impermanente en tiempo real, y recibe alertas inteligentes por Telegram y Email cuando necesites rebalancear.

## 🎯 **Características Principales**

| Feature | Descripción |
|---------|-------------|
| 🔍 **Monitoreo Automático** | Rastrea todas tus posiciones V3 cada 4 horas |
| 📊 **Cálculo de IL** | Pérdida impermanente vs fees en tiempo real |
| ⚠️ **Alertas Inteligentes** | Notificaciones cuando sales del rango |
| 💰 **Tracking de Fees** | Monitorea fees no reclamados |
| 📈 **APR Real** | Calcula rentabilidad real (fees - IL) |
| 🔄 **Sugerencias de Rebalanceo** | IA recomienda optimizaciones |
| 📱 **Multi-canal** | Telegram + Email con diseño profesional |

## 🚀 **Quick Start**

```bash
# 1. Clonar repo
git clone https://github.com/anthonysurfermx/uniswap-v3-ai-agent.git
cd uniswap-v3-ai-agent

# 2. Ejecutar setup automático
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Importar workflow en n8n
# Archivo: workflows/Uniswap-Monitor-V3.V1.json

# 4. Configurar APIs y ejecutar
```

## 📋 **Requisitos**

- **n8n** (self-hosted o cloud)
- **Moralis API key** (Plan Pro recomendado)
- **OpenAI API key**
- **Telegram Bot Token**
- **Gmail OAuth credentials**
- **Google Sheets API access**

## ⚙️ **Instalación Detallada**

### 1. Configurar Google Sheets
Crea una hoja con estas columnas:
| wallet_address | position_notes | alert_threshold |
|----------------|----------------|-----------------|
| 0x123... | "Main LP wallet" | 10 |
| 0x456... | "Test wallet" | 15 |

### 2. Configurar APIs

**Moralis**
```bash
Header: X-API-Key
Value: tu_moralis_api_key
```

**OpenAI**
```bash
API Key: tu_openai_api_key
Model: gpt-4o-mini
```

**Telegram**
```bash
Bot Token: tu_bot_token
Chat ID: tu_chat_id
```

## 📊 **Métricas Calculadas**

### Pérdida Impermanente
```
IL = (1 - (2 * √(price_ratio)) / (1 + price_ratio)) * 100
```

### APR Real
```
Real APR = Fee APR - IL%
```

### Eficiencia de Rango
```
Efficiency = (Tiempo en Rango / Tiempo Total) * 100
```

## 🚨 **Tipos de Alertas**

- **🔴 Críticas**: Posición fuera de rango > 3 días
- **🟡 Advertencias**: IL > 10% o cerca del límite
- **🟢 Informativas**: Fees no reclamados > $100
- **💡 Sugerencias**: Oportunidad de rebalanceo detectada

## 📈 **Casos de Uso**

- **LPs Profesionales**: Gestión de múltiples posiciones concentradas
- **Fondos DeFi**: Monitoreo de capital de inversores
- **Yield Optimizers**: Maximizar generación de fees vs IL
- **Gestores de Riesgo**: Seguimiento de exposición en pools

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 **Licencia**
Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 🙏 **Agradecimientos**

- **Uniswap Labs** por el protocolo V3
- **Moralis** por la API DeFi
- **n8n** por la plataforma de automatización
- **OpenAI** por GPT-4o

## ⭐ **Roadmap**

- [ ] Dashboard web nativo
- [ ] Soporte multi-cadena
- [ ] Backtesting de estrategias
- [ ] Integración con DEX agregadores
- [ ] API REST propia
- [ ] Mobile app

---

**⚡ ¿Te gusta el proyecto? ¡Dale una estrella ⭐ y compártelo!**

*Construido con ❤️ para la comunidad DeFi*
