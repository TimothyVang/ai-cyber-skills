# Language ecosystems (Cloud X Berry)

Read when choosing a language or runtime, setting up a project's build, test, or debug tooling, or working in an unfamiliar language and needing its runtime model, concurrency model, and traps. The one-line pick-by-domain table is in `backend-system-design.md`; this file has the depth. Source keys are in `README.md`.

## Runtime model at a glance

| Language | Execution | Memory management | Concurrency |
|---|---|---|---|
| C | AOT native: preprocess → compile (GCC, Clang, MSVC) → assemble → link | Manual `malloc`/`free`; stack + heap; no GC | OS threads (pthreads), C11 `<threads.h>` and `stdatomic.h` |
| C++ | AOT native (GCC/libstdc++, Clang/libc++, MSVC/STL) | RAII, `unique_ptr` (single owner), `shared_ptr` (ref-counted); no GC | Threads, mutexes, atomics, async tasks; no compiler race safety |
| Rust | AOT native via `rustc` on LLVM; one self-contained binary | Ownership, borrowing, lifetimes checked at compile time: many shared refs or one mutable ref; no GC | Type system blocks data races; Tokio for async I/O |
| Go | AOT single static binary, no host runtime needed | Concurrent low-latency tracing GC; escape analysis moves values to the heap | Goroutines multiplexed onto few OS threads, typed channels |
| Java | `javac` → bytecode → JVM interprets and JITs (OpenJDK, Oracle, Corretto) | Tracing GC (G1, ZGC); bounds-checked arrays | Platform threads plus Java 21 virtual threads for cheap I/O concurrency |
| C# / .NET | Roslyn → CIL → CLR JIT (.NET 10 LTS) | Tracing GC; structs on the stack; `unsafe` pointers for interop | `async`/`await` on the thread pool, Task Parallel Library |
| Python | CPython compiles to `.pyc` bytecode, runs on its VM; no build step | Reference counting plus a cycle collector; everything is a heap object; assignment copies the reference | `asyncio` event loop for I/O; the GIL limits CPU threads, so use processes for multi-core |
| JavaScript / TypeScript | V8, SpiderMonkey, JavaScriptCore: bytecode plus JIT on hot paths; TS type-checks then transpiles to JS | Tracing GC; objects, arrays, closures on the heap | One thread plus event loop (microtasks, macrotasks); Web Workers or Worker Threads for CPU work |
| PHP | Zend Engine compiles to opcodes per request; OpCache speeds it up | Ref counting plus cycle GC; memory is per request and freed when the response ends | Many worker processes (PHP-FPM), not threads |
| Ruby | YARV bytecode VM | Mark-and-sweep GC; everything is an object | Global VM lock in MRI; multi-process servers (Puma) |
| Kotlin | Compiles to JVM bytecode; also JS and native via Kotlin Multiplatform | JVM GC (ART on Android); null safety in the type system (`Type?`) | Coroutines |
| Swift | AOT native on LLVM | ARC, no GC; value types with copy-on-write; `weak` and `unowned` break cycles | `async`/`await`, actors isolate mutable state, task groups |

(C-ECO, CPP-ECO, RUST-ECO, GO-4MIN, JAVA-ECO, CSHARP, PY-ECO, JS-ECO, FRAMEWORKS-2026, LANGS-2026)

## Tooling

| Language | Packages and build | Main frameworks and libraries | Test, lint, debug |
|---|---|---|---|
| C | No standard package manager; CMake, Make, Ninja; Conan, vcpkg, or OS packages | glibc, musl, newlib; OpenSSL, FreeRTOS, Zephyr | GDB, LLDB; clang-tidy, cppcheck; ASan, UBSan; libFuzzer, AFL |
| C++ | CMake generating Make or Ninja; vcpkg, Conan | STL, Boost, Qt, C++20 modules | GoogleTest, Catch2; GDB, LLDB, VS debugger; clang-format; TSan, ASan, UBSan |
| Rust | Cargo, crates.io, `Cargo.lock` | Axum (HTTP), SQLx (compile-time checked SQL), Serde, Tokio | `cargo test`, Clippy, rustfmt, cargo-audit |
| Go | Go modules (`go.mod`); `go build`, `go fmt`, `go test` | Large stdlib (`net/http`) | `go test`, `-race` detector, Delve |
| Java | Maven (`pom.xml`) or Gradle; Maven Central | Spring Boot, Spring Data JPA, Hibernate, Jackson; Micronaut, Quarkus | JUnit, Mockito; IntelliJ, Eclipse; Actuator, Micrometer |
| C# | .NET CLI, NuGet, `.csproj` | ASP.NET Core, EF Core, Blazor, .NET MAUI, .NET Aspire | xUnit, NUnit; Visual Studio, Rider, VS Code C# Dev Kit; profilers |
| Python | pip and PyPI; `requirements.txt` or Poetry; `venv` | FastAPI, Django, Flask; PyTorch, TensorFlow, Transformers, Pandas, NumPy | pytest, unittest; Ruff, Flake8, Black; PyCharm, VS Code |
| JS / TS | npm, pnpm, Yarn; Vite (Rolldown), Webpack, Bun | React, Next.js, Vue; Express, NestJS, Fastify, Koa; Zod | Vitest, Jest, Playwright; ESLint, Prettier; browser DevTools |
| PHP | Composer, Packagist | Laravel (auth, routing, Eloquent), Symfony | PHPUnit, Pest; Xdebug |
| Ruby | RubyGems, Bundler (`Gemfile.lock`) | Rails, Sinatra | RSpec, Minitest; Pry |
| Kotlin | Gradle or Maven | Ktor, Spring Boot; Jetpack Compose | JUnit, MockK; IntelliJ, Android Studio |
| Swift | Swift Package Manager | SwiftUI, UIKit; Vapor (server) | XCTest, Swift Testing; LLDB in Xcode |

## Where each shines, and the traps

| Language | Built with it | Choose for | Avoid for | Traps |
|---|---|---|---|---|
| C | Linux kernel, SQLite, Git, cURL, PostgreSQL, Redis, CPython | Kernels, drivers, microcontrollers, hard real-time | Web APIs, business apps, anything where memory-safety risk is not justified | Buffer overflows, leaks, use-after-free, undefined behavior |
| C++ | Unreal Engine, Chrome, Firefox, PyTorch backend, HFT | Game and browser engines, ML runtimes, hot paths | Small CLIs, CRUD backends, quick prototypes | Complex syntax, slow template-heavy builds, no ABI stability across compilers, UB |
| Rust | Cloudflare Pingora (trillions of requests a day), parts of Linux, Android components, Hugging Face tokenizers | Proxies, network infrastructure, security-critical services, fast AI utilities, CLIs | Throwaway scripts, early exploration, simple business apps | Steep learning curve with the borrow checker, lifetimes, slow builds on big codebases |
| Go | Docker, Kubernetes, Terraform, the TypeScript 7 compiler | Cloud-native infrastructure, DevOps tools, microservices, distributed systems | GPU ML research, AAA games, mobile front ends | No inheritance; repetitive `if err != nil`; slices share their backing array unless copied |
| Java | Banking, airline booking, Kafka, Minecraft | Big enterprise backends, financial platforms, streaming | Sub-ms cold-start serverless, tiny embedded, bare metal | High baseline memory, slow cold start, leaks from collections that never drop references |
| C# | Azure services, Unity scripts, WPF and WinForms apps | Enterprise APIs, Azure backends, MAUI apps, Unity games | Drivers, microcontrollers | .NET Framework vs Core vs .NET naming confusion, heavier runtime than Go or Rust |
| Python | AI research, LangChain, LangGraph, Instagram | AI and ML, data work, automation, FastAPI services | 3D engines, mobile apps, kernels | Slow CPU-bound code, runtime type errors, mutable default arguments, the GIL |
| JS / TS | Web front ends, Electron (VS Code, Slack, Discord), Cloudflare Workers | Web apps, full stack, real-time event backends, desktop tools | Scientific computing, model training, low-latency systems | Type coercion quirks, npm supply-chain risk, CPU work blocks the single thread, promise confusion |
| PHP | WordPress, Wikipedia, e-commerce | Portals, stores, CMS, business web apps | Real-time games, systems infrastructure, ML pipelines | Inconsistent legacy functions, framework boot cost per request without persistent workers, poor fit for long-lived sockets |
| Ruby | GitHub, Shopify, Basecamp, Airbnb (early) | Startup MVPs, fast iteration, CRUD apps | High-throughput streaming, big data, low-latency finance | Slow CPU, metaprogramming that makes large codebases hard to trace, high memory |
| Kotlin | Android (Google's preferred language), JVM backends | Native Android, a modern Java replacement | Systems programming, places that cannot run a JVM | Slower compiles than Java, small ecosystem outside JVM and Android, coroutine debugging |
| Swift | iOS, iPadOS, macOS, watchOS, visionOS apps | Apple client apps | Cross-platform web services, non-Apple servers | Weak server adoption, breaking changes in early versions, leaks from strong reference cycles |
