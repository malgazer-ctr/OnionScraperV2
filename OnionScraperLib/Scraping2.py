# site_data.py

class SiteData:
    def __init__(self, url, site_category, is_active, comment):
        self.url = url
        self.site_category = site_category
        self.is_active = is_active
        self.comment = comment

    def process(self):
        print(f"Processing {self.__class__.__name__}:")
        print(f"URL: {self.url}")
        print(f"Category: {self.site_category}")
        print(f"Active: {self.is_active}")
        print(f"Comment: {self.comment}")
        print("Custom processing for this site type")
        print()

class LockBit3_0_2024_7(SiteData):
    def process(self):
        super().process()
        print("Additional processing for LockBit3.0_2024_7")

class NITROGEN(SiteData):
    def process(self):
        super().process()
        print("Additional processing for NITROGEN")

# data.py

# from site_data import LockBit3_0_2024_7, NITROGEN

sites = {
    "LockBit3.0_2024_7": LockBit3_0_2024_7(
        url="http://lockbitapt2d73krlbewgv27tquljgxr33xbwwsp6rkyieto7u4ncead.onion/",
        site_category="LeakSite(Mirror)",
        is_active="Active",
        comment="2024/10/1追加。"
    ),
    "NITROGEN": LockBit3_0_2024_7(
        url="http://nitrogenczslprh3xyw6lh5xyjvmsz7ciljoqxxknd7uymkfetfhgvqd.onion",
        site_category="LeakSite(Mirror)",
        is_active="Active",
        comment="2024/10/1追加。"
    )
}

# main.py

# from data import sites

def process_sites():
    for site_name, site_object in sites.items():
        site_object.process()

if __name__ == "__main__":
    process_sites()