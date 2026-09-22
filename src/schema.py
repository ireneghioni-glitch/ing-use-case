from pydantic import BaseModel
from typing import Optional


class AssetMetadata(BaseModel):
    '''
    Metadata for a single asset (web page or ad) in the ING Youth Acquisition
    Communication Comparator dataset.

    This class defines the structure for each asset collected during scraping.
    It includes identifiers, bank information, page role, audience labels,
    eligibility criteria, and file paths. Used to validate raw metadata from the 
    Data Collection phase and to ensure consistency across the entire pipeline.

    Attributes:
        asset_id (str): Unique identifier for the asset.
        bank (str): Name of the bank (e.g., "ING", "KBC").
        bank_type (str): "traditional" or "challenger".
        channel (str): "website" or "ad".
        asset_role (str): Role of the page, e.g., "youth_landing", "adult_landing".
        audience_label (str): Target audience, e.g., "youth_18_25", "general_adult".
        audience_evidence (Optional[str]): Text snippet supporting the audience label.
        eligibility_age_min (Optional[int]): Minimum age for the offer.
        eligibility_age_max (Optional[int]): Maximum age for the offer.
        student_requirement (Optional[bool]): Whether student status is required.
        overlap_with_18_25 (Optional[str]): Description of overlap with 18-25 range.
        pair_id (Optional[str]): Links matched youth/adult pages.
        url (str): Source URL of the asset.
        language (str): Language code (e.g., "en", "nl", "fr").
        collected_at (str): Date of collection in ISO format.
        raw_html_path (str): Path to the raw HTML file.
        screenshot_path (Optional[str]): Path to the screenshot image.
    '''
    asset_id: str
    bank: str
    bank_type:str
    channel: str
    audience_label: str
    audience_evidence: Optional[str] = None
    eligibility_age_min: Optional[int] = None
    eligibility_age_max: Optional[int] = None
    student_requirement: Optional[bool] = None
    overlap_with_18_25: Optional[str] = None
    pair_id: Optional[str] = None
    url: str
    language: str
    collected_at: str
    raw_html_path: str
    screenshot_path: Optional[str] = None
    text: Optional[str] = None


class FeatureRecord(BaseModel):
    '''
    Represents a single feature value extracted for one asset.

    Each record corresponds to one feature (e.g., 'main_benefit',
    'jargon_density') for one asset. It includes the extracted value, missing
    status if applicable, evidence, extraction method, and versioning
    information to ensure reproducibility.

    Attributes:
        asset_id (str): Foreign key linking to AssetMetadata.asset_id.
        feature_name (str): Name of the feature, e.g., "main_benefit".
        value (str): Extracted value (can be numeric, binary, or categorical).
        missing_status (Optional[str]): "unknown", "not_applicable", etc.
        missing_reason (Optional[str]): Reason for missing value, e.g., "robots_disallowed".
        evidence_text (Optional[str]): Text snippet supporting the value.
        evidence_location (Optional[str]): Location of evidence, e.g., "hero section".
        method (str): Extraction method: "deterministic", "llm", or "manual".
        codebook_version (str): Version of the codebook used.
        prompt_version (Optional[str]): Version of the LLM prompt used.
        review_status (str): "pending", "validated", or "rejected".
    '''
    asset_id: str
    feature_name: str
    value: str                              # numeric, binary or categorical
    missing_status: Optional[str] = None    # "unknown", "not_applicable", etc.
    missing_reason: Optional[str] = None    # "robots_disallowed", etc.
    evidence_text: Optional[str] = None
    evidence_location: Optional[str] = None
    method: str                             # "deterministic", "llm", "manual"
    codebook_version: str
    prompt_version: Optional[str] = None
    review_status: str                      # "pending", "validated", "rejected"


class LLMOutput(BaseModel):
    '''
    Schema for validating the JSON output from a large language model (LLM)
    when extracting interpretive features.

    This class ensures the LLM returns a structured response with the feature
    name, value, supporting evidence text and location, and reasoning. Used to
    prevent hallucinations and maintain data quality when using LLMs for
    feature extraction (e.g., main benefit, tone, persuasive framing).

    Attributes:
        feature (str): Name of the feature being classified.
        value (str): The classified value (must be from allowed list).
        evidence_text (str): Exact sentence from the source text supporting the value.
        evidence_location (str): Location of evidence in the page (e.g., "hero", "footer").
        reasoning (str): Brief explanation of why this value was chosen.
    '''
    feature: str
    value: str
    evidence_text: str
    evidence_location: str
    reasoning: str


