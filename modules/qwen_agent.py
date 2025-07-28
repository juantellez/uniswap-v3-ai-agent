import json
import logging
import re
from llama_cpp import Llama
from core.config import settings
from models.metric import PositionMetric

logger = logging.getLogger(__name__)

class QwenAgent:
    def __init__(self, model_path: str, n_gpu_layers: int):
        """
        Inicializa el agente y carga el modelo LLM.
        """
        logger.info(f"Cargando modelo LLM desde: {model_path}")
        try:
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=4096,
                verbose=False
            )
            logger.info("Modelo LLM cargado exitosamente.")
        except Exception as e:
            logger.error(f"Error fatal al cargar el modelo LLM: {e}", exc_info=True)
            self.model = None

    def _build_prompt(self, metric: PositionMetric) -> str:
        position = metric.position
        
        # PROMPT v3 - Pidiendo concisión en el razonamiento
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
            <|im_end|>
            <|im_start|>assistant
            <thinking>
            El precio actual está fuera del rango superior. La posición no genera comisiones. Se necesita rebalancear para volver al rango activo.
            </thinking>
            <final_answer>
            {{
            "action": "REBALANCE",
            "justification": "El precio actual ha superado el límite superior. Se recomienda rebalancear a un nuevo rango para continuar generando comisiones."
            }}
            </final_answer><|im_end|>
            <|im_start|>user
            Perfecto. Ahora analiza esta nueva posición:
            - Pool: {position.token0_symbol}/{position.token1_symbol}
            - Rango de precios: {metric.price_lower:.4f} - {metric.price_upper:.4f}
            - Precio actual: {metric.current_price:.4f}
            - Estado: {'En Rango' if metric.is_in_range else 'Fuera de Rango'}
            <|im_end|>
            <|im_start|>assistant
            """
        return prompt_template

    def _parse_output(self, raw_text: str) -> dict:
        """
        Extrae el JSON de la etiqueta <final_answer> usando expresiones regulares.
        """
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