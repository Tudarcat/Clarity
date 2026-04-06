'''
   Copyright 2026 Yuyang Shen

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
Knowledge repository-related tools for the agent system.
"""

from typing import List
import json
from agent.tool.tool_base import ToolBase, ToolParameter


class KnowledgeRepo(ToolBase):
    """
    Tool for suggesting where and how to search for information.
    This tool does not fetch the final content. It only returns search routing suggestions.
    """

    @property
    def name(self) -> str:
        return "knowledge_repo"

    @property
    def description(self) -> str:
        return (
            "Suggest suitable websites, sources, and search strategies for a user's query. "
            "Use this tool before web search when you need to know where to search."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The user's original question or search topic.",
                required=True
            ),
            ToolParameter(
                name="task_type",
                type="string",
                description=(
                    "Optional task type hint, such as 'paper_search', 'web_search', "
                    "'code_lookup', 'project_lookup', 'weather_search', 'news_search', "
                    "'file_lookup', or 'planning'."
                ),
                required=False,
                default=""
            ),
            ToolParameter(
                name="domain_hint",
                type="string",
                description=(
                    "Optional domain hint to narrow the search area, such as "
                    "'ai', 'unity', 'python', 'academic', 'project_internal', "
                    "'weather', 'news', 'file', or 'planning'."
                ),
                required=False,
                default=""
            ),
            ToolParameter(
                name="top_k",
                type="integer",
                description="Maximum number of suggested search routes to return. Default is 3.",
                required=False,
                default=3
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)

        raw_query = kwargs.get("query", "")
        query = raw_query.lower()# 转换为小写，用于后续匹配匹配,后续无需添加lower()方法
        task_type = kwargs.get("task_type", "").lower()
        domain_hint = kwargs.get("domain_hint", "").lower()
        top_k = kwargs.get("top_k", 3)

        suggestions = self._route_query(query, task_type, domain_hint)

        output = []
        output.append("Knowledge Search Routing Result")
        output.append("=" * 50)
        output.append(f"Query: {raw_query}")
        output.append(f"Task Type: {task_type or 'N/A'}")
        output.append(f"Domain Hint: {domain_hint or 'N/A'}")
        output.append("-" * 50)

        if suggestions:
            first_sites = suggestions[0].get("sites", [])
            site_names = []
            for site in first_sites:
                if isinstance(site, dict):
                    site_names.append(site.get("name", "Unknown"))
                else:
                    site_names.append(str(site))
            output.append(f"Recommended Sites: {', '.join(site_names)}")
            output.append("-" * 50)
        else:
            output.append("Recommended Sites: N/A")
            output.append("-" * 50)

        for i, item in enumerate(suggestions[:top_k], 1):
            output.append(f"[{i}] Source Type: {item['source_type']}")
            output.append(f"Suggested Query Templates: {', '.join(item['query_templates'])}")
            output.append(f"Reason: {item['reason']}")
            output.append("-" * 50)

        return "\n".join(output)

    def _route_query(self, query: str, task_type: str, domain_hint: str):
        """
        Return routing suggestions based on query/task/domain.
        """
        """
        4.2
        添加了例如天气查询的路由规则
        添加了priority字段，用于确定搜索路由的优先级，
        由于只返回top_k条建议，所以优先级越高，建议的路由越优先,便于后续添加新的路由匹配规则
        手动设置字段优先级,后续可以改为自动根据匹配规则和任务类型动态调整
        """

        """
        4.6
        修正了在execute中在定义item之前就访问了item['sites']导致的bug,导致调用工具报错
        """
        rules = [
            # 1. Weather
            {
                "priority": 85,
                "match": lambda q, t, d: (
                    "天气" in q or
                    "气温" in q or
                    "温度" in q or
                    "降雨" in q or
                    "下雨" in q or
                    "下雪" in q or
                    "风力" in q or
                    "空气质量" in q or
                    "weather" in q or
                    "temperature" in q or
                    "forecast" in q or
                    "rain" in q or
                    "snow" in q or
                    "wind" in q or
                    t == "weather_search" or
                    d == "weather"
                ),
                "source_type": "weather_search",
                "sites": [
                    {
                        "name": "中国天气网",
                        "url": "http://www.weather.com.cn",
                        "search_url_template": "http://toy1.weather.com.cn/search?cityname={query}",
                        "search_hint": "城市名 + 天气"
                    },
                    {
                        "name": "中央气象台",
                        "url": "http://www.nmc.cn",
                        "search_url_template": "http://www.nmc.cn/publish/forecast.html",
                        "search_hint": "城市天气预报"
                    }
                ],
                "query_templates": [
                    query,
                    f"{query} 天气预报",
                    f"{query} 中国天气网",
                    f"{query} 中央气象台",
                    f"{query} weather forecast"
                ],
                "reason": (
                    "This looks like a weather lookup task. "
                    "Official or authoritative forecast sources should be preferred, "
                    "and city-level forecast pages are more useful than generic homepages."
                )
            },

            # 2. Academic papers
            {
                "priority": 90,
                "match": lambda q, t, d: (
                    "paper" in q or
                    "论文" in q or
                    "survey" in q or
                    "review" in q or
                    t == "paper_search" or
                    d == "academic"
                ),
                "source_type": "academic_search",
                "sites": [
                    {
                        "name": "Crossref",
                        "url": "https://api.crossref.org/works",
                        "search_hint": "paper keywords"
                        
                    },
                    {
                        "name": "arXiv",
                        "url": "https://arxiv.org/search",
                        "search_hint": "paper keywords"
                    },
                    {
                        "name": "Google Scholar",
                        "url": "https://scholar.google.com/scholar",
                        "search_hint": "paper keywords"
                    }
                ],
                "query_templates": [
                    query,
                    f"{query} survey",
                    f"{query} review"
                ],
                "reason": "This looks like an academic paper search task."
            },

            # 3. News
            {
                "priority": 60,
                "match": lambda q, t, d: (
                    "新闻" in q or
                    "news" in q or
                    "时事" in q or
                    t == "news_search" or
                    d == "news"
                ),
                "source_type": "news_search",
                "sites": [
                    {
                        "name": "新华社",
                        "url": "http://www.xinhuanet.com",
                        "search_hint": "关键词 + 新闻"
                    },
                    {
                        "name": "人民网",
                        "url": "http://www.people.com.cn",
                        "search_hint": "关键词 + 时政 新闻"
                    },
                    {
                        "name": "BBC News",
                        "url": "https://www.bbc.com/news",
                        "search_hint": "keyword + news"
                    },
                    {
                        "name": "Reuters",
                        "url": "https://www.reuters.com",
                        "search_hint": "keyword + latest news"
                    },
                    {
                        "name": "微博热搜",
                        "url": "https://s.weibo.com/top/summary",
                        "search_hint": "查看实时热点榜单"
                    },
                    {
                        "name": "今日头条",
                        "url": "https://www.toutiao.com",
                        "search_hint": "关键词 + 热点"
                    }
                ],
                "query_templates": [
                    query,
                    f"{query} 最新 新闻",
                    f"{query} 热点 事件",
                    f"{query} latest news"
                ],
                "reason": "This looks like a news or current-events lookup task."
            },

            # 4. Python / PyTorch
            {
                "priority": 70,
                "match": lambda q, t, d: (
                    d == "python" or
                    "python" in q or
                    "pytorch" in q or
                    ".py" in q
                ),
                "source_type": "programming_docs",
                "sites": ["Python Docs", "PyTorch Docs", "GitHub"],
                "query_templates": [
                    query,
                    f"site:docs.python.org {query}",
                    f"site:pytorch.org {query}"
                ],
                "reason": "This looks like a Python or PyTorch-related programming task."
            },

            # 5. Local file / PDF / directory
            {
                "priority": 70,
                "match": lambda q, t, d: (
                    "pdf" in q or
                    "文件" in q or
                    "目录" in q or
                    "readme" in q or
                    t == "file_lookup" or
                    d == "file"
                ),
                "source_type": "file_lookup",
                "sites": ["Local Filesystem", "PDF Reader", "Project Directory"],
                "query_templates": [
                    query,
                    f"{query} local file",
                    f"{query} pdf"
                ],
                "reason": "This looks like a local file or PDF lookup task."
            },

            # 6. Project internal
            {
                "priority": 40,
                "match": lambda q, t, d: (
                    t == "project_lookup" or
                    d == "project_internal"
                ),
                "source_type": "project_internal",
                "sites": ["Local Repository", "Project Docs", "README", "Source Code"],
                "query_templates": [
                    query,
                    f"{query} in repo",
                    f"{query} source code"
                ],
                "reason": "This looks like a project-internal lookup task."
            },

            # 7. Planning / multi-step task
            {
                "priority": 30,
                "match": lambda q, t, d: (
                    "步骤" in q or
                    "计划" in q or
                    "流程" in q or
                    t == "planning" or
                    d == "planning"
                ),
                "source_type": "planning_task",
                "sites": ["Task Planner", "Internal Plan Tool"],
                "query_templates": [
                    query,
                    f"{query} step by step",
                    f"{query} plan"
                ],
                "reason": "This looks like a planning or multi-step task."
            },
           # 8. Travelling Recommendation
            {
                "priority": 75,
                "match": lambda q, t, d: (
                    "旅行" in q or
                    "旅游" in q or
                    "攻略" in q or
                    "recommend" in q or
                    t == "travelling_recommend" or
                    d == "travelling_recommend"
                ),
                "source_type": "travelling_recommend",
                "sites": [
                    {
                        "name": "马蜂窝",
                        "url": "https://www.mafengwo.cn/search/q.php?q={query}",# 搜索框
                        "search_hint": "目的地 + 旅游 攻略"
                    },
                    {
                        "name": "携程旅行",
                        "url": "https://www.ctrip.com/search?q={query}",
                        "search_hint": "目的地 + 酒店 景点"
                    },
                    {
                        "name": "穷游网",
                        "url": "https://www.qyer.com/search?q={query}",# 搜索框
                        "search_hint": "目的地 + 自由行 攻略"
                    },
                    {
                        "name": "TripAdvisor",
                        "url": "https://www.tripadvisor.com/search?q={query}",
                        "search_hint": "destination + things to do"
                    },
                    {
                        "name": "Google Maps",
                        "url": "https://maps.google.com/search?q={query}",
                        "search_hint": "地点 + 景点 餐厅"
                    }
                ],
                "query_templates": [
                    query,
                    f"{query} 旅游 攻略",
                    f"{query} 景点 推荐",
                    f"{query} travel guide",
                    f"{query} things to do"
                ],
                "reason": "This looks like a travelling recommendation or planning task."
            },

            # 9. Default fallback
            {
                "priority": 10,
                "match": lambda q, t, d: True,
                "source_type": "default_fallback",
                "sites": ["Official Documentation", "Authoritative Sources", "General Web Search"],
                "query_templates": [
                    query,
                    f"{query} official",
                    f"{query} documentation"
                ],
                "reason": "No specific routing rule matched exactly, so start from official or authoritative sources."
            }
        ]

        matched = []
        for rule in rules:
            if rule["match"](query, task_type, domain_hint):
                matched.append(rule)

        matched.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return matched