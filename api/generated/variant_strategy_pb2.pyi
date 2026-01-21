from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VariantCharacteristics(_message.Message):
    __slots__ = ("name", "description", "visual_focus", "messaging_style", "best_for", "platform_fit", "ctr_lift_potential", "conversion_lift", "engagement_lift", "average_cpv", "optimal_duration_seconds", "color_intensity", "design_complexity")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VISUAL_FOCUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGING_STYLE_FIELD_NUMBER: _ClassVar[int]
    BEST_FOR_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIT_FIELD_NUMBER: _ClassVar[int]
    CTR_LIFT_POTENTIAL_FIELD_NUMBER: _ClassVar[int]
    CONVERSION_LIFT_FIELD_NUMBER: _ClassVar[int]
    ENGAGEMENT_LIFT_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_CPV_FIELD_NUMBER: _ClassVar[int]
    OPTIMAL_DURATION_SECONDS_FIELD_NUMBER: _ClassVar[int]
    COLOR_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    DESIGN_COMPLEXITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    visual_focus: str
    messaging_style: str
    best_for: _containers.RepeatedScalarFieldContainer[str]
    platform_fit: _containers.RepeatedScalarFieldContainer[str]
    ctr_lift_potential: float
    conversion_lift: float
    engagement_lift: float
    average_cpv: str
    optimal_duration_seconds: int
    color_intensity: str
    design_complexity: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., visual_focus: _Optional[str] = ..., messaging_style: _Optional[str] = ..., best_for: _Optional[_Iterable[str]] = ..., platform_fit: _Optional[_Iterable[str]] = ..., ctr_lift_potential: _Optional[float] = ..., conversion_lift: _Optional[float] = ..., engagement_lift: _Optional[float] = ..., average_cpv: _Optional[str] = ..., optimal_duration_seconds: _Optional[int] = ..., color_intensity: _Optional[str] = ..., design_complexity: _Optional[str] = ...) -> None: ...

class VariantInPortfolio(_message.Message):
    __slots__ = ("variant_id", "variant_type", "name", "budget_allocation", "current_performance", "impressions", "clicks", "ctr", "conversions", "conversion_rate", "status", "created_at", "updated_at")
    VARIANT_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BUDGET_ALLOCATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PERFORMANCE_FIELD_NUMBER: _ClassVar[int]
    IMPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    CLICKS_FIELD_NUMBER: _ClassVar[int]
    CTR_FIELD_NUMBER: _ClassVar[int]
    CONVERSIONS_FIELD_NUMBER: _ClassVar[int]
    CONVERSION_RATE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    variant_id: str
    variant_type: str
    name: str
    budget_allocation: float
    current_performance: float
    impressions: int
    clicks: int
    ctr: float
    conversions: int
    conversion_rate: float
    status: str
    created_at: str
    updated_at: str
    def __init__(self, variant_id: _Optional[str] = ..., variant_type: _Optional[str] = ..., name: _Optional[str] = ..., budget_allocation: _Optional[float] = ..., current_performance: _Optional[float] = ..., impressions: _Optional[int] = ..., clicks: _Optional[int] = ..., ctr: _Optional[float] = ..., conversions: _Optional[int] = ..., conversion_rate: _Optional[float] = ..., status: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ...) -> None: ...

class Portfolio(_message.Message):
    __slots__ = ("portfolio_id", "name", "brand", "product", "total_budget", "variants", "status", "total_impressions", "total_clicks", "portfolio_ctr", "total_conversions", "portfolio_conversion_rate", "created_at", "updated_at", "performance_metrics")
    class PerformanceMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BRAND_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BUDGET_FIELD_NUMBER: _ClassVar[int]
    VARIANTS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_IMPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CLICKS_FIELD_NUMBER: _ClassVar[int]
    PORTFOLIO_CTR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CONVERSIONS_FIELD_NUMBER: _ClassVar[int]
    PORTFOLIO_CONVERSION_RATE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    PERFORMANCE_METRICS_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    name: str
    brand: str
    product: str
    total_budget: float
    variants: _containers.RepeatedCompositeFieldContainer[VariantInPortfolio]
    status: str
    total_impressions: float
    total_clicks: float
    portfolio_ctr: float
    total_conversions: float
    portfolio_conversion_rate: float
    created_at: str
    updated_at: str
    performance_metrics: _containers.ScalarMap[str, float]
    def __init__(self, portfolio_id: _Optional[str] = ..., name: _Optional[str] = ..., brand: _Optional[str] = ..., product: _Optional[str] = ..., total_budget: _Optional[float] = ..., variants: _Optional[_Iterable[_Union[VariantInPortfolio, _Mapping]]] = ..., status: _Optional[str] = ..., total_impressions: _Optional[float] = ..., total_clicks: _Optional[float] = ..., portfolio_ctr: _Optional[float] = ..., total_conversions: _Optional[float] = ..., portfolio_conversion_rate: _Optional[float] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ..., performance_metrics: _Optional[_Mapping[str, float]] = ...) -> None: ...

class CreatePortfolioRequest(_message.Message):
    __slots__ = ("name", "brand", "product", "total_budget", "variant_types", "variant_budgets")
    class VariantBudgetsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    BRAND_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BUDGET_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TYPES_FIELD_NUMBER: _ClassVar[int]
    VARIANT_BUDGETS_FIELD_NUMBER: _ClassVar[int]
    name: str
    brand: str
    product: str
    total_budget: float
    variant_types: _containers.RepeatedScalarFieldContainer[str]
    variant_budgets: _containers.ScalarMap[str, float]
    def __init__(self, name: _Optional[str] = ..., brand: _Optional[str] = ..., product: _Optional[str] = ..., total_budget: _Optional[float] = ..., variant_types: _Optional[_Iterable[str]] = ..., variant_budgets: _Optional[_Mapping[str, float]] = ...) -> None: ...

class GetPortfolioRequest(_message.Message):
    __slots__ = ("portfolio_id",)
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    def __init__(self, portfolio_id: _Optional[str] = ...) -> None: ...

class ListPortfoliosRequest(_message.Message):
    __slots__ = ("brand", "limit", "offset")
    BRAND_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    brand: str
    limit: int
    offset: int
    def __init__(self, brand: _Optional[str] = ..., limit: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class ListPortfoliosResponse(_message.Message):
    __slots__ = ("portfolios", "total")
    PORTFOLIOS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    portfolios: _containers.RepeatedCompositeFieldContainer[Portfolio]
    total: int
    def __init__(self, portfolios: _Optional[_Iterable[_Union[Portfolio, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class UpdatePortfolioRequest(_message.Message):
    __slots__ = ("portfolio_id", "name", "total_budget", "status", "variant_budgets")
    class VariantBudgetsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BUDGET_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VARIANT_BUDGETS_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    name: str
    total_budget: float
    status: str
    variant_budgets: _containers.ScalarMap[str, float]
    def __init__(self, portfolio_id: _Optional[str] = ..., name: _Optional[str] = ..., total_budget: _Optional[float] = ..., status: _Optional[str] = ..., variant_budgets: _Optional[_Mapping[str, float]] = ...) -> None: ...

class PortfolioResponse(_message.Message):
    __slots__ = ("success", "message", "portfolio")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PORTFOLIO_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    portfolio: Portfolio
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., portfolio: _Optional[_Union[Portfolio, _Mapping]] = ...) -> None: ...

class GetVariantLibraryRequest(_message.Message):
    __slots__ = ("variant_type",)
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    variant_type: str
    def __init__(self, variant_type: _Optional[str] = ...) -> None: ...

class VariantLibraryResponse(_message.Message):
    __slots__ = ("variants",)
    class VariantsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VariantCharacteristics
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VariantCharacteristics, _Mapping]] = ...) -> None: ...
    VARIANTS_FIELD_NUMBER: _ClassVar[int]
    variants: _containers.MessageMap[str, VariantCharacteristics]
    def __init__(self, variants: _Optional[_Mapping[str, VariantCharacteristics]] = ...) -> None: ...

class GetVariantRecommendationRequest(_message.Message):
    __slots__ = ("campaign_type", "target_audience", "platform", "goal")
    CAMPAIGN_TYPE_FIELD_NUMBER: _ClassVar[int]
    TARGET_AUDIENCE_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    GOAL_FIELD_NUMBER: _ClassVar[int]
    campaign_type: str
    target_audience: str
    platform: str
    goal: str
    def __init__(self, campaign_type: _Optional[str] = ..., target_audience: _Optional[str] = ..., platform: _Optional[str] = ..., goal: _Optional[str] = ...) -> None: ...

class VariantRecommendation(_message.Message):
    __slots__ = ("variant_type", "variant_name", "recommendation_score", "reasoning", "characteristics")
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_NAME_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_SCORE_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    CHARACTERISTICS_FIELD_NUMBER: _ClassVar[int]
    variant_type: str
    variant_name: str
    recommendation_score: float
    reasoning: str
    characteristics: VariantCharacteristics
    def __init__(self, variant_type: _Optional[str] = ..., variant_name: _Optional[str] = ..., recommendation_score: _Optional[float] = ..., reasoning: _Optional[str] = ..., characteristics: _Optional[_Union[VariantCharacteristics, _Mapping]] = ...) -> None: ...

class VariantRecommendationResponse(_message.Message):
    __slots__ = ("recommendations", "explanation")
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    recommendations: _containers.RepeatedCompositeFieldContainer[VariantRecommendation]
    explanation: str
    def __init__(self, recommendations: _Optional[_Iterable[_Union[VariantRecommendation, _Mapping]]] = ..., explanation: _Optional[str] = ...) -> None: ...

class AddVariantRequest(_message.Message):
    __slots__ = ("portfolio_id", "variant_type", "budget_allocation", "custom_props")
    class CustomPropsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    BUDGET_ALLOCATION_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_PROPS_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    variant_type: str
    budget_allocation: float
    custom_props: _containers.ScalarMap[str, str]
    def __init__(self, portfolio_id: _Optional[str] = ..., variant_type: _Optional[str] = ..., budget_allocation: _Optional[float] = ..., custom_props: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RemoveVariantRequest(_message.Message):
    __slots__ = ("portfolio_id", "variant_id")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_ID_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    variant_id: str
    def __init__(self, portfolio_id: _Optional[str] = ..., variant_id: _Optional[str] = ...) -> None: ...

class SampleSizeRequest(_message.Message):
    __slots__ = ("baseline_rate", "minimum_detectable_effect", "alpha", "power")
    BASELINE_RATE_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_DETECTABLE_EFFECT_FIELD_NUMBER: _ClassVar[int]
    ALPHA_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    baseline_rate: float
    minimum_detectable_effect: float
    alpha: float
    power: float
    def __init__(self, baseline_rate: _Optional[float] = ..., minimum_detectable_effect: _Optional[float] = ..., alpha: _Optional[float] = ..., power: _Optional[float] = ...) -> None: ...

class SampleSizeResponse(_message.Message):
    __slots__ = ("sample_size_per_variant", "total_sample_size", "explanation")
    SAMPLE_SIZE_PER_VARIANT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    sample_size_per_variant: int
    total_sample_size: int
    explanation: str
    def __init__(self, sample_size_per_variant: _Optional[int] = ..., total_sample_size: _Optional[int] = ..., explanation: _Optional[str] = ...) -> None: ...

class CreateExperimentRequest(_message.Message):
    __slots__ = ("portfolio_id", "experiment_name", "variant_control", "variant_test", "duration_days", "significance_level")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    VARIANT_CONTROL_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TEST_FIELD_NUMBER: _ClassVar[int]
    DURATION_DAYS_FIELD_NUMBER: _ClassVar[int]
    SIGNIFICANCE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    experiment_name: str
    variant_control: str
    variant_test: _containers.RepeatedScalarFieldContainer[str]
    duration_days: int
    significance_level: float
    def __init__(self, portfolio_id: _Optional[str] = ..., experiment_name: _Optional[str] = ..., variant_control: _Optional[str] = ..., variant_test: _Optional[_Iterable[str]] = ..., duration_days: _Optional[int] = ..., significance_level: _Optional[float] = ...) -> None: ...

class Experiment(_message.Message):
    __slots__ = ("experiment_id", "portfolio_id", "name", "control_variant", "test_variants", "status", "created_at", "started_at", "ended_at", "duration_days")
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTROL_VARIANT_FIELD_NUMBER: _ClassVar[int]
    TEST_VARIANTS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    ENDED_AT_FIELD_NUMBER: _ClassVar[int]
    DURATION_DAYS_FIELD_NUMBER: _ClassVar[int]
    experiment_id: str
    portfolio_id: str
    name: str
    control_variant: str
    test_variants: _containers.RepeatedScalarFieldContainer[str]
    status: str
    created_at: str
    started_at: str
    ended_at: str
    duration_days: int
    def __init__(self, experiment_id: _Optional[str] = ..., portfolio_id: _Optional[str] = ..., name: _Optional[str] = ..., control_variant: _Optional[str] = ..., test_variants: _Optional[_Iterable[str]] = ..., status: _Optional[str] = ..., created_at: _Optional[str] = ..., started_at: _Optional[str] = ..., ended_at: _Optional[str] = ..., duration_days: _Optional[int] = ...) -> None: ...

class ExperimentResponse(_message.Message):
    __slots__ = ("success", "message", "experiment")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    experiment: Experiment
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class AnalyzeExperimentRequest(_message.Message):
    __slots__ = ("experiment_id", "variant_conversions", "variant_exposures")
    class VariantConversionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class VariantExposuresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_CONVERSIONS_FIELD_NUMBER: _ClassVar[int]
    VARIANT_EXPOSURES_FIELD_NUMBER: _ClassVar[int]
    experiment_id: str
    variant_conversions: _containers.ScalarMap[str, int]
    variant_exposures: _containers.ScalarMap[str, int]
    def __init__(self, experiment_id: _Optional[str] = ..., variant_conversions: _Optional[_Mapping[str, int]] = ..., variant_exposures: _Optional[_Mapping[str, int]] = ...) -> None: ...

class ExperimentAnalysis(_message.Message):
    __slots__ = ("variant", "conversion_rate", "lift", "confidence_interval_lower", "confidence_interval_upper", "p_value", "is_significant", "recommendation")
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    CONVERSION_RATE_FIELD_NUMBER: _ClassVar[int]
    LIFT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_INTERVAL_LOWER_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_INTERVAL_UPPER_FIELD_NUMBER: _ClassVar[int]
    P_VALUE_FIELD_NUMBER: _ClassVar[int]
    IS_SIGNIFICANT_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    variant: str
    conversion_rate: float
    lift: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    is_significant: bool
    recommendation: str
    def __init__(self, variant: _Optional[str] = ..., conversion_rate: _Optional[float] = ..., lift: _Optional[float] = ..., confidence_interval_lower: _Optional[float] = ..., confidence_interval_upper: _Optional[float] = ..., p_value: _Optional[float] = ..., is_significant: bool = ..., recommendation: _Optional[str] = ...) -> None: ...

class ExperimentAnalysisResponse(_message.Message):
    __slots__ = ("analysis", "winner", "winner_confidence", "summary")
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    WINNER_FIELD_NUMBER: _ClassVar[int]
    WINNER_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    analysis: _containers.RepeatedCompositeFieldContainer[ExperimentAnalysis]
    winner: str
    winner_confidence: float
    summary: str
    def __init__(self, analysis: _Optional[_Iterable[_Union[ExperimentAnalysis, _Mapping]]] = ..., winner: _Optional[str] = ..., winner_confidence: _Optional[float] = ..., summary: _Optional[str] = ...) -> None: ...

class OptimizationRequest(_message.Message):
    __slots__ = ("portfolio_id",)
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    def __init__(self, portfolio_id: _Optional[str] = ...) -> None: ...

class OptimizationResponse(_message.Message):
    __slots__ = ("success", "message", "recommendations")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    recommendations: _containers.RepeatedCompositeFieldContainer[OptimizationRecommendation]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., recommendations: _Optional[_Iterable[_Union[OptimizationRecommendation, _Mapping]]] = ...) -> None: ...

class OptimizationRecommendation(_message.Message):
    __slots__ = ("variant", "action", "recommended_allocation", "reasoning", "expected_impact")
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_ALLOCATION_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_IMPACT_FIELD_NUMBER: _ClassVar[int]
    variant: str
    action: str
    recommended_allocation: float
    reasoning: str
    expected_impact: float
    def __init__(self, variant: _Optional[str] = ..., action: _Optional[str] = ..., recommended_allocation: _Optional[float] = ..., reasoning: _Optional[str] = ..., expected_impact: _Optional[float] = ...) -> None: ...

class CaptureInsightRequest(_message.Message):
    __slots__ = ("portfolio_id", "insight_type", "variant", "description", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    INSIGHT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    insight_type: str
    variant: str
    description: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, portfolio_id: _Optional[str] = ..., insight_type: _Optional[str] = ..., variant: _Optional[str] = ..., description: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class InsightResponse(_message.Message):
    __slots__ = ("success", "insight_id", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    INSIGHT_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    insight_id: str
    message: str
    def __init__(self, success: bool = ..., insight_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class GetInsightsRequest(_message.Message):
    __slots__ = ("portfolio_id", "variant", "limit")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    variant: str
    limit: int
    def __init__(self, portfolio_id: _Optional[str] = ..., variant: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class Insight(_message.Message):
    __slots__ = ("insight_id", "portfolio_id", "variant", "type", "description", "created_at", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    INSIGHT_ID_FIELD_NUMBER: _ClassVar[int]
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    insight_id: str
    portfolio_id: str
    variant: str
    type: str
    description: str
    created_at: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, insight_id: _Optional[str] = ..., portfolio_id: _Optional[str] = ..., variant: _Optional[str] = ..., type: _Optional[str] = ..., description: _Optional[str] = ..., created_at: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GetInsightsResponse(_message.Message):
    __slots__ = ("insights",)
    INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    insights: _containers.RepeatedCompositeFieldContainer[Insight]
    def __init__(self, insights: _Optional[_Iterable[_Union[Insight, _Mapping]]] = ...) -> None: ...

class LearnFromCampaignRequest(_message.Message):
    __slots__ = ("portfolio_id", "final_metrics", "outcome")
    class FinalMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    FINAL_METRICS_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    final_metrics: _containers.ScalarMap[str, float]
    outcome: str
    def __init__(self, portfolio_id: _Optional[str] = ..., final_metrics: _Optional[_Mapping[str, float]] = ..., outcome: _Optional[str] = ...) -> None: ...

class LearningResponse(_message.Message):
    __slots__ = ("success", "message", "key_learnings", "recommendations_for_next")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    KEY_LEARNINGS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATIONS_FOR_NEXT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    key_learnings: _containers.RepeatedScalarFieldContainer[str]
    recommendations_for_next: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., key_learnings: _Optional[_Iterable[str]] = ..., recommendations_for_next: _Optional[_Iterable[str]] = ...) -> None: ...

class OptimizePortfolioRequest(_message.Message):
    __slots__ = ("portfolio_id", "optimization_goal", "constraints")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    OPTIMIZATION_GOAL_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINTS_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    optimization_goal: str
    constraints: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, portfolio_id: _Optional[str] = ..., optimization_goal: _Optional[str] = ..., constraints: _Optional[_Iterable[str]] = ...) -> None: ...

class BudgetAllocationRequest(_message.Message):
    __slots__ = ("portfolio_id", "total_budget", "allocation_strategy")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BUDGET_FIELD_NUMBER: _ClassVar[int]
    ALLOCATION_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    total_budget: float
    allocation_strategy: str
    def __init__(self, portfolio_id: _Optional[str] = ..., total_budget: _Optional[float] = ..., allocation_strategy: _Optional[str] = ...) -> None: ...

class BudgetAllocation(_message.Message):
    __slots__ = ("variant", "allocated_budget", "allocation_percentage", "reasoning")
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_BUDGET_FIELD_NUMBER: _ClassVar[int]
    ALLOCATION_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    variant: str
    allocated_budget: float
    allocation_percentage: float
    reasoning: str
    def __init__(self, variant: _Optional[str] = ..., allocated_budget: _Optional[float] = ..., allocation_percentage: _Optional[float] = ..., reasoning: _Optional[str] = ...) -> None: ...

class BudgetAllocationResponse(_message.Message):
    __slots__ = ("allocations", "total_budget", "strategy")
    ALLOCATIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BUDGET_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    allocations: _containers.RepeatedCompositeFieldContainer[BudgetAllocation]
    total_budget: float
    strategy: str
    def __init__(self, allocations: _Optional[_Iterable[_Union[BudgetAllocation, _Mapping]]] = ..., total_budget: _Optional[float] = ..., strategy: _Optional[str] = ...) -> None: ...

class DeploymentStrategyRequest(_message.Message):
    __slots__ = ("portfolio_id", "total_duration_days", "initial_percent")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DURATION_DAYS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_PERCENT_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    total_duration_days: int
    initial_percent: int
    def __init__(self, portfolio_id: _Optional[str] = ..., total_duration_days: _Optional[int] = ..., initial_percent: _Optional[int] = ...) -> None: ...

class DeploymentPhase(_message.Message):
    __slots__ = ("phase_number", "name", "start_day", "end_day", "active_variants", "variant_budgets", "description")
    class VariantBudgetsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PHASE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    START_DAY_FIELD_NUMBER: _ClassVar[int]
    END_DAY_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_VARIANTS_FIELD_NUMBER: _ClassVar[int]
    VARIANT_BUDGETS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    phase_number: int
    name: str
    start_day: int
    end_day: int
    active_variants: _containers.RepeatedScalarFieldContainer[str]
    variant_budgets: _containers.ScalarMap[str, float]
    description: str
    def __init__(self, phase_number: _Optional[int] = ..., name: _Optional[str] = ..., start_day: _Optional[int] = ..., end_day: _Optional[int] = ..., active_variants: _Optional[_Iterable[str]] = ..., variant_budgets: _Optional[_Mapping[str, float]] = ..., description: _Optional[str] = ...) -> None: ...

class DeploymentStrategyResponse(_message.Message):
    __slots__ = ("phases", "overall_strategy", "key_milestones")
    PHASES_FIELD_NUMBER: _ClassVar[int]
    OVERALL_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    KEY_MILESTONES_FIELD_NUMBER: _ClassVar[int]
    phases: _containers.RepeatedCompositeFieldContainer[DeploymentPhase]
    overall_strategy: str
    key_milestones: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, phases: _Optional[_Iterable[_Union[DeploymentPhase, _Mapping]]] = ..., overall_strategy: _Optional[str] = ..., key_milestones: _Optional[_Iterable[str]] = ...) -> None: ...

class ImageValidationRequest(_message.Message):
    __slots__ = ("portfolio_id", "variant_type", "image_path", "use_mock")
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_PATH_FIELD_NUMBER: _ClassVar[int]
    USE_MOCK_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    variant_type: str
    image_path: str
    use_mock: bool
    def __init__(self, portfolio_id: _Optional[str] = ..., variant_type: _Optional[str] = ..., image_path: _Optional[str] = ..., use_mock: bool = ...) -> None: ...

class CLIPValidationResult(_message.Message):
    __slots__ = ("product_confidence", "safety_score", "quality_score", "brand_fit", "composition", "overall_score", "is_approved", "recommendations", "variant_checks", "detected_objects", "detected_concepts", "safety_flags")
    class VariantChecksEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bool
        def __init__(self, key: _Optional[str] = ..., value: bool = ...) -> None: ...
    PRODUCT_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SAFETY_SCORE_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    BRAND_FIT_FIELD_NUMBER: _ClassVar[int]
    COMPOSITION_FIELD_NUMBER: _ClassVar[int]
    OVERALL_SCORE_FIELD_NUMBER: _ClassVar[int]
    IS_APPROVED_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    VARIANT_CHECKS_FIELD_NUMBER: _ClassVar[int]
    DETECTED_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    DETECTED_CONCEPTS_FIELD_NUMBER: _ClassVar[int]
    SAFETY_FLAGS_FIELD_NUMBER: _ClassVar[int]
    product_confidence: float
    safety_score: float
    quality_score: float
    brand_fit: float
    composition: float
    overall_score: float
    is_approved: bool
    recommendations: _containers.RepeatedScalarFieldContainer[str]
    variant_checks: _containers.ScalarMap[str, bool]
    detected_objects: _containers.RepeatedScalarFieldContainer[str]
    detected_concepts: _containers.RepeatedScalarFieldContainer[str]
    safety_flags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, product_confidence: _Optional[float] = ..., safety_score: _Optional[float] = ..., quality_score: _Optional[float] = ..., brand_fit: _Optional[float] = ..., composition: _Optional[float] = ..., overall_score: _Optional[float] = ..., is_approved: bool = ..., recommendations: _Optional[_Iterable[str]] = ..., variant_checks: _Optional[_Mapping[str, bool]] = ..., detected_objects: _Optional[_Iterable[str]] = ..., detected_concepts: _Optional[_Iterable[str]] = ..., safety_flags: _Optional[_Iterable[str]] = ...) -> None: ...

class ImageValidationResponse(_message.Message):
    __slots__ = ("success", "message", "validation")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    validation: CLIPValidationResult
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., validation: _Optional[_Union[CLIPValidationResult, _Mapping]] = ...) -> None: ...

class PortfolioValidationRequest(_message.Message):
    __slots__ = ("portfolio_id", "variant_image_paths", "use_mock")
    class VariantImagePathsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    VARIANT_IMAGE_PATHS_FIELD_NUMBER: _ClassVar[int]
    USE_MOCK_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    variant_image_paths: _containers.ScalarMap[str, str]
    use_mock: bool
    def __init__(self, portfolio_id: _Optional[str] = ..., variant_image_paths: _Optional[_Mapping[str, str]] = ..., use_mock: bool = ...) -> None: ...

class VariantImageQualityResult(_message.Message):
    __slots__ = ("variant", "validation", "quality_tier")
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    QUALITY_TIER_FIELD_NUMBER: _ClassVar[int]
    variant: str
    validation: CLIPValidationResult
    quality_tier: str
    def __init__(self, variant: _Optional[str] = ..., validation: _Optional[_Union[CLIPValidationResult, _Mapping]] = ..., quality_tier: _Optional[str] = ...) -> None: ...

class PortfolioValidationResponse(_message.Message):
    __slots__ = ("success", "message", "variant_results", "quality_scores")
    class QualityScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_RESULTS_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    variant_results: _containers.RepeatedCompositeFieldContainer[VariantImageQualityResult]
    quality_scores: _containers.ScalarMap[str, float]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., variant_results: _Optional[_Iterable[_Union[VariantImageQualityResult, _Mapping]]] = ..., quality_scores: _Optional[_Mapping[str, float]] = ...) -> None: ...

class QualityReportRequest(_message.Message):
    __slots__ = ("portfolio_id",)
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    def __init__(self, portfolio_id: _Optional[str] = ...) -> None: ...

class QualityReportResponse(_message.Message):
    __slots__ = ("report", "quality_tiers", "quality_scores")
    class QualityTiersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class QualityScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    REPORT_FIELD_NUMBER: _ClassVar[int]
    QUALITY_TIERS_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORES_FIELD_NUMBER: _ClassVar[int]
    report: str
    quality_tiers: _containers.ScalarMap[str, str]
    quality_scores: _containers.ScalarMap[str, float]
    def __init__(self, report: _Optional[str] = ..., quality_tiers: _Optional[_Mapping[str, str]] = ..., quality_scores: _Optional[_Mapping[str, float]] = ...) -> None: ...

class DeploymentRecommendationRequest(_message.Message):
    __slots__ = ("portfolio_id", "quality_scores")
    class QualityScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PORTFOLIO_ID_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORES_FIELD_NUMBER: _ClassVar[int]
    portfolio_id: str
    quality_scores: _containers.ScalarMap[str, float]
    def __init__(self, portfolio_id: _Optional[str] = ..., quality_scores: _Optional[_Mapping[str, float]] = ...) -> None: ...

class DeploymentRecommendation(_message.Message):
    __slots__ = ("variant", "status", "recommended_budget", "improvement_steps")
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_BUDGET_FIELD_NUMBER: _ClassVar[int]
    IMPROVEMENT_STEPS_FIELD_NUMBER: _ClassVar[int]
    variant: str
    status: str
    recommended_budget: float
    improvement_steps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, variant: _Optional[str] = ..., status: _Optional[str] = ..., recommended_budget: _Optional[float] = ..., improvement_steps: _Optional[_Iterable[str]] = ...) -> None: ...

class DeploymentRecommendationResponse(_message.Message):
    __slots__ = ("recommendations", "summary")
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    recommendations: _containers.RepeatedCompositeFieldContainer[DeploymentRecommendation]
    summary: str
    def __init__(self, recommendations: _Optional[_Iterable[_Union[DeploymentRecommendation, _Mapping]]] = ..., summary: _Optional[str] = ...) -> None: ...
