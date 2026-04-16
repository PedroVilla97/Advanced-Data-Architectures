import csv
import random
import httpx

#Reputation-service on port 8002 from docker-compose.yml
reputation_service_url = "http://localhost:8002"


#known skills to match on
known_skills = ["python", "fastapi", "react", "typescript", "docker","firebase", "sql", "gcp", "bigquery", "firestore","next.js", "node.js",]


def clean_skills_data(raw_skills):
    clean_skill_lst = []

    if not raw_skills:
        return []

    else:
        raw_skills = raw_skills.split(",")
        for skill in raw_skills:
            skill = skill.strip().lower()
            clean_skill_lst.append(skill)

    return clean_skill_lst


def creating_hourly_rate(experience_years):

    #There is no data about salary, so this is synthetic data based on experience
    if experience_years <= 2:
        mean = 25
    elif experience_years <= 5:
        mean = 35
    elif experience_years <= 8:
        mean = 50
    else:
        mean = 70

    #Create random factor
    spread = random.uniform(-5, 5)
    return round(mean + spread, 2)


def creating_reputation_score(experience_years):
    # There is also no data about reputation score, so this is also synthetic data based on experience from 3 to 5

    # max = 3 + 2 = 5
    mean = 3 + (experience_years * 0.2)
    spread = random.uniform(-0.3, 0.3)
    score = mean + spread
    # Keep score within 3 to 5
    final_score = round(max(3.0, min(5.0, score)), 2)

    return final_score


def has_relevant_skills(skills):
    # Checking if freelancers has a needed skill
    for skill in skills:
        if skill in known_skills:
            return True

    return False



def load_freelancers_data(filepath):
    #Loading freelancers dataset and creating freelancer profiles for the backend

    freelancers = []
    counter = 1

    with open(filepath, newline="", encoding="utf-8") as csvfile:
        #Creeate dictionary for every row
        reader = csv.DictReader(csvfile)

        for row in reader:

            # Call cleaning function
            skills = clean_skills_data(row["Skills"])

            # Check if freelancer has relevant skills
            if not has_relevant_skills(skills):
                continue

            experience = int(row["Experience_Years"])

            # Creating profile as the backend needs
            profile = {
                "freelancer_id": f"f{counter}",
                "name": row["Name"],
                "skills": skills,
                "hourly_rate": creating_hourly_rate(experience),
                "reputation_score": creating_reputation_score(experience),
            }

            freelancers.append(profile)
            counter += 1

    return freelancers


def seed_backend(freelancers):

    match = 0
    skipped = 0

    for profile in freelancers:

        response = httpx.post(
            f"{reputation_service_url}/profiles",
            json=profile,
            timeout=5.0
        )

        if response.status_code == 200:
            print(f"  ✓ {profile['name']} added with freelancer_id: {profile['freelancer_id']})")
            match += 1
        elif response.status_code == 409:
            print(f"{profile['name']} duplicate, so skipped")
            skipped += 1
        else:
            print(f"Error {profile['name']}: {response.status_code} {response.text}")


    return

if __name__ == "__main__":
    freelancers = load_freelancers_data("data/resume_dataset_1200.csv")
    seed_backend(freelancers)