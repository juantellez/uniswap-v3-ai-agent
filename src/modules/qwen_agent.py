import os
import sys
import json
import logging
import re
import requests
from tqdm import tqdm
from llama_cpp import Llama
from core.config import settings
from models.metric import PositionMetric

logger = logging.getLogger(__name__)

class QwenAgent:
    def __init__(self, model_path: str, n_gpu_layers: int):
        """
        Inicializa el agente. Comprueba si el modelo existe, si no, lo descarga.
        Luego, carga el modelo LLM.
        """
        self.model_path = model_path
        self.model_download_url = "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q8_0.gguf"
        
        # Paso 1: Descargar el modelo si es necesario
        self._download_model_if_not_exists()

        # Paso 2: Cargar el modelo
        logger.info(f"Cargando modelo LLM desde: {self.model_path}")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=4096,
                verbose=False
            )
            logger.info("Modelo LLM cargado exitosamente.")
        except Exception as e:
            logger.error(f"Error fatal al cargar el modelo LLM: {e}", exc_info=True)
            # Salir si el modelo no se puede cargar, ya que la aplicación no puede funcionar.
            sys.exit(1)

    def _download_model_if_not_exists(self):
        """Comprueba la existencia del modelo y lo descarga si no está presente."""
        if os.path.exists(self.model_path):
            logger.info(f"El modelo LLM ya existe en: {self.model_path}")
            return

        logger.warning(f"El modelo LLM no se encuentra en '{self.model_path}'.")
        logger.info(f"Iniciando descarga desde: {self.model_download_url}")

        model_dir = os.path.dirname(self.model_path)
        os.makedirs(model_dir, exist_ok=True)
        
        try:
            with requests.get(self.model_download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size_in_bytes = int(r.headers.get('content-length', 0))
                block_size = 1024 * 8 # 8 Kibibytes

                with tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc=f"Descargando {os.path.basename(self.model_path)}") as bar:
                    with open(self.model_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=block_size):
                            bar.update(len(chunk))
                            f.write(chunk)
            
            if total_size_in_bytes != 0 and bar.n != total_size_in_bytes:
                raise IOError("ERROR, la descarga del modelo se interrumpió.")

            logger.info("Descarga del modelo completada exitosamente.")

        except Exception as e:
            logger.error(f"Fallo en la descarga del modelo: {e}", exc_info=True)
            # Si hay un archivo parcial, lo borramos para intentar de nuevo la próxima vez.
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            raise RuntimeError(f"No se pudo descargar el modelo desde {self.model_download_url}") from e


    def _build_prompt(self, metric: PositionMetric) -> str:
        position = metric.position
        
        prompt_template = f"""<|im_start|>system
        Eres un analista experto en DeFi. Tu proceso es:
        1.  Primero, razona de forma CONCISA sobre la posición dentro de las etiquetas <thinking>.
        2.  Después, proporciona tu recomendación final como un objeto JSON dentro de las etiquetas <final_answer>.

        **Constraint:** La etiqueta <final_answer> y su contenido JSON DEBEN ser lo último en tu respuesta.<|im_end|>
        <|im_start|>user
        Analiza la siguiente posición:
        - Pool: WBTC/WETH
        - Rango de precios: 15.5000 - 18.5000
        - Precio actual: 19.2000
        - Estado: Fuera de Rango
        - Pérdida Impermanente (IL): -2.5%

        **Tu Tarea:**
        Responde con un objeto JSON que contenga "action" y "justification".<|im_end|>
        <|im_start|>assistant
        <thinking>
        El precio actual está fuera del rango superior. La posición no genera comisiones y tiene una pérdida impermanente del 2.5%. Se necesita rebalancear para volver al rango activo.
        </thinking>
        <final_answer>
        {{
        "action": "REBALANCE",
        "justification": "El precio actual ha superado el límite superior y la posición tiene una IL de -2.5%. Se recomienda rebalancear para volver a generar comisiones."
        }}
        </final_answer><|im_end|>
        <|im_start|>user
        Perfecto. Ahora analiza esta nueva posición:
        - Pool: {position.token0_symbol}/{position.token1_symbol}
        - Rango de precios: {metric.price_lower:.4f} - {metric.price_upper:.4f}
        - Precio actual: {metric.current_price:.4f}
        - Estado: {'En Rango' if metric.is_in_range else 'Fuera de Rango'}
        - Pérdida Impermanente (IL): {metric.impermanent_loss_percent:.2f}%

        **Tu Tarea:**
        Responde con un objeto JSON que contenga "action" y "justification".<|im_end|>
        <|im_start|>assistant
        """
        return prompt_template

    def _parse_output(self, raw_text: str) -> dict:
        # ... (Este método se mantiene igual) ...
        match = re.search(r"<final_answer>(.*?)</final_answer>", raw_text, re.DOTALL)
        if not match:
            logger.warning("La IA no generó la etiqueta <final_answer>.")
            return {"action": "FORMAT_ERROR", "justification": "La IA no siguió el formato de salida con etiquetas.", "raw_output": raw_text}
        json_str = match.group(1).strip()
        try:
            parsed_json = json.loads(json_str)
            return {"action": parsed_json.get("action", "UNKNOWN"), "justification": parsed_json.get("justification", "No justification provided."), "raw_output": raw_text}
        except json.JSONDecodeError:
            logger.warning(f"La IA generó un JSON inválido dentro de <final_answer>: {json_str}")
            return {"action": "PARSE_ERROR", "justification": "La IA generó un JSON inválido.", "raw_output": raw_text}

    def generate_recommendation(self, metric: PositionMetric) -> dict:
        # ... (Este método se mantiene igual) ...
        if not self.model:
            return {"action": "ERROR", "justification": "El modelo LLM no está cargado.", "raw_output": ""}
        prompt = self._build_prompt(metric)
        try:
            output = self.model(
                prompt, 
                max_tokens=2048, 
                stop=["</final_answer>"],
                temperature=0.2, 
                echo=False
            )
            raw_text = output['choices'][0]['text'] + "</final_answer>"
            return self._parse_output(raw_text)
        except Exception as e:
            logger.error(f"Error durante la generación de la IA: {e}", exc_info=True)
            return {"action": "GENERATION_ERROR", "justification": str(e), "raw_output": ""}

# Instancia global
qwen_agent = QwenAgent(model_path=settings.MODEL_PATH, n_gpu_layers=settings.N_GPU_LAYERS)