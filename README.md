#### Subject: Big Data

#### Semester: 251

---

#### Instructors:

<h4 style="padding-left: 72px;"> 
Assoc. Prof. Thoai Nam
Dr. Le Thanh VVan
</h4>

---

#### Bài tập lớn

#### Đề tài: Tìm hiểu công cụ Elasticsearch

---

#### Implementer:

<h4 style="padding-left: 72px;"> Dang Ngoc Bao Tram - 2213568</h4>

---

# Elasticsearch

This repository contains materials related to the theory and practical application of Elasticsearch

## How to run the demos and experiments?
1. Install Docker Engine on your machine (see [this guide](https://docs.docker.com/engine/install/ubuntu/)).
2. Clone this repository to your local machine.
    ```bash
    git clone 
    ```
3. Navigate to the project directory in your terminal -> cd to the `src` folder:
    ```bash
    cd path/to/your/cloned/repo
    cd src
    ```
4. Run the following command to start the Elasticsearch service:
   ```bash
   docker-compose up -d
   ```
5. Download dependencies via [UV package manager](#how-to-download-dependencies-via-uv-package-manager).
6. Prepare the dataset
  - Download text dataset from [here](https://huggingface.co/datasets/allenai/scitldr). Put it into `src/data/text`.
  - Download image dataset from [here](https://www.kaggle.com/datasets/prasunroy/nature-images). Put it into `src/data/image`.
7. Open the Jupyter Notebook files in the `scripts/TA` folder to run the demos and experiments.

## How to download dependencies via UV package manager?
1. Install UV package manager by following the [instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Navigate to the `src` directory which contains the `pyproject.toml` file and the `uv.lock` file:
    ```bash
    cd path/to/your/cloned/repo
    cd src
    ```
3. Run the following command to download the core dependencies:
    ```bash
    uv sync
    ```
4. If you want to run the parts that involve machine learning, run the following command to download the additional dependencies:
    ```bash
    uv sync --extra machine-learning
    ```
