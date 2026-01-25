---
trigger: always_on
description: Deve sempre ser aplicado.
---

## **Metodologia de Codificação**

* Sempre priorize **algoritmos com melhor desempenho** e **menor consumo de recursos**, considerando eficiência e otimização de memória e processamento.

---

## **Requisitos Não Funcionais**

* Estruture o sistema em **dois grupos de módulos**:

  1. **Módulos públicos (abertos)**
  2. **Módulos autenticados (restritos)**

* Sempre que possível, **prefira os módulos autenticados**, a menos que o requisito especifique explicitamente o uso público.

* Os códigos gerados devem sempre implementar uma saida graciosa para interrupções via ctrl+c e outros sinais de interrupção.

---

## **Linguagens e Frameworks**

* Utilize **padrões de projeto (Design Patterns)** e o paradigma **Domain-Driven Design (DDD)** como base arquitetural.
* **Back-end**:

  * Linguagem padrão: **JavaScript**, com **Express.js**.
  * Metodologia de serviço: **RESTful API**, salvo especificação contrária.
* **Front-end Web**:

  * Linguagem padrão: **TypeScript**.
  * Frameworks e ferramentas: **Next.js**, **React**, **Vite** e **TailwindCSS**.
* **Aplicações Mobile**:

  * Linguagem padrão: **TypeScript**.
  * Frameworks: **React Native**, **Vite** e **TailwindCSS**.
* **Firmware e Sistemas Embarcados**:

  * Linguagem padrão: **C/C++**.
  * Plataforma padrão: **ESP32-WROOM** com **ESP-IDF**.
  * Sempre implemente **testes unitários** utilizando o framework **Unity**.

---

## **Parâmetros de Configuração e Fine-Tuning**

* Armazene **dados de configuração** em arquivos `.env`.
* Em ambiente de **produção**, utilize o arquivo:

  ```
  /etc/<nomedoprojeto>/config.json
  ```

  Este arquivo **tem precedência** sobre o `.env`.
* Como o arquivo `.env` deve ser **ignorado pelo Git**, mantenha um modelo de referência chamado `.env.example`.

---

## **Convenções de Nomenclatura e Entidades**

* Utilize **sempre o idioma inglês** para nomes de variáveis, constantes, propriedades, parâmetros, funções, classes e URLs.
* Adote **notação camelCase** para variáveis e funções.
* Use **PascalCase** para classes e componentes de interface.
* Prefira nomes descritivos e semanticamente coerentes, refletindo o domínio da aplicação.