"""HunyuanVideo 1.5 license activation policy, defense in depth.

This is NOT legal certification or reliable geoblocking. The deployment
coordinator must independently verify Tencent's then-current actual terms,
AUP, all distribution territories, recipients, provider notices and identities.
"""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import MotionError

# European Union members (ISO 3166-1 alpha-2), UK, South Korea.
EXCLUDED_COUNTRIES = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
    "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
    "RO", "SK", "SI", "ES", "SE", "GB", "KR",
})
LICENSE_URL = "https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE"


@dataclass(frozen=True)
class HunyuanLicensePolicy:
    """Values must be loaded from verified operator/backend records.

    Owner approval permits DEV spend but does not issue Tencent license rights.
    This assertion is a required reviewed gate, not legal certification.
    """
    deployment_country: str
    retailer_country: str
    intended_publication_countries: tuple[str, ...]
    actual_provider_legal_name: str
    tencent_no_endorsement_notice: bool
    full_license_terms_available_to_users: bool
    acceptable_use_and_local_law_checked: bool
    commercial_media_rights_checked: bool
    operator_terms_reviewed: bool
    monthly_active_users_at_model_release: int
    separate_tencent_license_if_required: bool = False

    def assert_allowed(self) -> None:
        countries = (self.deployment_country, self.retailer_country,
                     *self.intended_publication_countries)
        if not countries or not self.intended_publication_countries:
            raise MotionError("Unreviewed deployment/publication territory")
        if any(type(c) is not str or len(c) != 2 or not c.isupper()
               or not c.isalpha() or c in EXCLUDED_COUNTRIES for c in countries):
            raise MotionError("Unlicensed Hunyuan territory or country")
        if (type(self.actual_provider_legal_name) is not str or
            not 3 <= len(self.actual_provider_legal_name.strip()) <= 180):
            raise MotionError("Actual video service provider disclosure missing")
        for gate in (self.tencent_no_endorsement_notice,
                     self.full_license_terms_available_to_users,
                     self.acceptable_use_and_local_law_checked,
                     self.commercial_media_rights_checked,
                     self.operator_terms_reviewed):
            if gate is not True:
                raise MotionError("Hunyuan commercial license obligation not reviewed")
        if (type(self.monthly_active_users_at_model_release) is not int or
            self.monthly_active_users_at_model_release < 0):
            raise MotionError("Licensing MAU eligibility unverified")
        if (self.monthly_active_users_at_model_release > 100_000_000 and
            self.separate_tencent_license_if_required is not True):
            raise MotionError("Separate Tencent commercial license required")
