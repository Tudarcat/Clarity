'''
   Copyright 2026 Yunda Wu

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''


"""
Configuration management for Clarity Agent.
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class ProviderConfig:
    """
    Configuration for a provider.
    """
    provider_type: str = ""
    model: str = ""
    api_url: str = ""
    api_key: Optional[str] = None


@dataclass
class Config:
    """
    Main configuration for Clarity Agent.
    """
    provider: ProviderConfig
    work_dir: str = "."
    max_iter: int = 20


class ConfigManager:
    """
    Manager for loading and saving configurations.
    """
    
    DEFAULT_CONFIG_PATH = Path.home() / ".clarity" / "config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
    
    def load_config(self) -> Optional[Config]:
        """
        Load configuration from file.
        
        :return: Config object if file exists, None otherwise.
        """
        if not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            provider_data = data.get("provider", {})
            provider_config = ProviderConfig(
                provider_type=provider_data.get("provider_type", "custom"),
                model=provider_data.get("model", ""),
                api_url=provider_data.get("api_url", ""),
                api_key=provider_data.get("api_key")
            )
            
            config = Config(
                provider=provider_config,
                work_dir=data.get("work_dir", "."),
                max_iter=data.get("max_iter", 20)
            )
            
            return config
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {str(e)}")
    
    def save_config(self, config: Config) -> None:
        """
        Save configuration to file.
        
        :param config: Config object to save.
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "provider": asdict(config.provider),
                "work_dir": config.work_dir,
                "max_iter": config.max_iter
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save config to {self.config_path}: {str(e)}")
    
    def create_default_config(self) -> Config:
        """
        Create a default configuration.
        
        :return: Default Config object.
        """
        provider_config = ProviderConfig()
        config = Config(provider=provider_config)
        return config
    
    def get_config_path(self) -> Path:
        """
        Get the path to the configuration file.
        
        :return: Path to the configuration file.
        """
        return self.config_path
