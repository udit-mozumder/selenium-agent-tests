Java Spring Boot Microservice Knowledge Base
Discount Management Service

Base Package: hp.onecloud

1. Architectural Principles (Industry Standard)
Core Principles

Clean Architecture / Hexagonal

Separation of Concerns

API-first design

Immutable DTOs

Validation at multiple layers

Stateless services

Observability-ready

Layering Model
Controller → Service → Domain → Repository

2. Standard Project Structure (MANDATORY)
src/main/java/hp/onecloud/discounts
│
├── DiscountsApplication.java
│
├── config/
│   ├── SecurityConfig.java
│   ├── MongoConfig.java
│   ├── OpenApiConfig.java
│   ├── JacksonConfig.java
│
├── controller/
│   ├── DiscountController.java
│
├── service/
│   ├── DiscountService.java
│   ├── impl/
│   │   └── DiscountServiceImpl.java
│
├── domain/
│   ├── model/
│   │   ├── Discount.java
│   │   ├── Market.java
│   │   ├── Partner.java
│   │   ├── ProductModel.java
│   │   ├── PlanBenefit.java
│   │
│   ├── enums/
│   │   └── DiscountType.java
│
├── repository/
│   ├── DiscountRepository.java
│   ├── specification/
│   │   └── DiscountSpecifications.java
│
├── dto/
│   ├── request/
│   │   └── DiscountFilterRequest.java
│   │
│   ├── response/
│   │   └── DiscountResponse.java
│
├── mapper/
│   └── DiscountResponseMapper.java
│
├── validation/
│   ├── DiscountValidator.java
│
├── exception/
│   ├── ApiError.java
│   ├── BadRequestException.java
│   ├── UnauthorizedException.java
│   ├── GlobalExceptionHandler.java
│
├── security/
│   ├── JwtAuthenticationFilter.java
│   ├── JwtTokenValidator.java
│
├── util/
│   ├── DateUtils.java
│
└── constants/
    └── ErrorMessages.java

3. Domain Layer (Business Truth)
Discount (Domain Model)

Represents pure business state

No HTTP / DB / framework logic

@Document(collection = "discounts")
public class Discount {

    @Id
    private ObjectId id;

    private String name;
    private String identifier;

    private Integer eligibilityWindowDays;

    private Instant startDate;
    private Instant endDate;

    private Market market;

    private boolean isDefault;

    private DiscountType discountType;

    private boolean environmentFlag;
    private boolean applicableGlobally;
    private boolean inactive;

    private List<Partner> partners;
    private List<ProductModel> productModels;
    private List<PlanBenefit> planBenefits;

    private Instant createdAt;
    private Instant updatedAt;
}

4. Enum Best Practice
public enum DiscountType {
    PRODUCT_ONLY,
    SERVICE_ONLY,
    PRODUCT_AND_SERVICE
}


✔ Enums ALWAYS uppercase
✔ Mapping handled in Jackson config

5. Repository Layer (MongoDB)
Repository
public interface DiscountRepository
        extends MongoRepository<Discount, ObjectId>,
                MongoSpecificationExecutor<Discount> {
}

Specification-Based Filtering (Best Practice)
public class DiscountSpecifications {

    public static Specification<Discount> activeOnly() {
        return (root, query, cb) ->
            cb.and(
                cb.greaterThan(root.get("endDate"), Instant.now()),
                cb.isFalse(root.get("inactive"))
            );
    }

    public static Specification<Discount> byMarketName(String market) {
        return (root, query, cb) ->
            cb.equal(root.get("market").get("name"), market);
    }

    public static Specification<Discount> byIdentifier(String identifier) {
        return (root, query, cb) ->
            cb.equal(root.get("identifier"), identifier);
    }

    public static Specification<Discount> byProductSku(String sku) {
        return (root, query, cb) ->
            cb.isMember(sku, root.get("productModels").get("sku"));
    }
}

6. Service Layer (Business Logic Owner)
Interface
public interface DiscountService {
    List<Discount> getDiscounts(DiscountFilterRequest request);
}

Implementation
@Service
public class DiscountServiceImpl implements DiscountService {

    private final DiscountRepository repository;

    @Override
    public List<Discount> getDiscounts(DiscountFilterRequest request) {

        DiscountValidator.validateProductSkuAndMarket(request);

        Specification<Discount> spec = Specification.where(null);

        if (!request.isExpired()) {
            spec = spec.and(DiscountSpecifications.activeOnly());
        }

        if (request.getMarket() != null) {
            spec = spec.and(DiscountSpecifications.byMarketName(request.getMarket()));
        }

        if (request.getIdentifier() != null) {
            spec = spec.and(DiscountSpecifications.byIdentifier(request.getIdentifier()));
        }

        if (request.getProductSku() != null) {
            spec = spec.and(DiscountSpecifications.byProductSku(request.getProductSku()));
        }

        return repository.findAll(spec);
    }
}

7. Controller Layer (API Boundary)
@RestController
@RequestMapping("/api/v1/discounts")
public class DiscountController {

    private final DiscountService service;
    private final DiscountResponseMapper mapper;

    @GetMapping
    public ResponseEntity<List<DiscountResponse>> getDiscounts(
            DiscountFilterRequest request) {

        List<Discount> discounts = service.getDiscounts(request);

        return ResponseEntity.ok(
            mapper.toResponse(discounts)
        );
    }
}

8. Validation Layer (Centralized)
public class DiscountValidator {

    public static void validateProductSkuAndMarket(DiscountFilterRequest request) {
        if (request.getProductSku() != null &&
            request.getMarket() == null) {
            throw new BadRequestException("Market is required");
        }
    }
}


✔ No validation logic in controller
✔ Reusable by batch jobs & agents

9. DTOs (Immutable)
public record DiscountFilterRequest(
    String market,
    String identifier,
    Boolean environmentFlag,
    String productSku,
    boolean expired
) {}

10. Mapper Layer (Serialization Control)
@Component
public class DiscountResponseMapper {

    public List<DiscountResponse> toResponse(List<Discount> discounts) {
        return discounts.stream()
                .map(this::map)
                .toList();
    }

    private DiscountResponse map(Discount d) {
        return new DiscountResponse(
            d.getId().toHexString(),
            d.getName(),
            d.getIdentifier(),
            d.getEligibilityWindowDays(),
            d.getStartDate().toString(),
            d.getEndDate().toString(),
            d.getMarket().getName(),
            d.isDefault(),
            d.getDiscountType().name().toLowerCase(),
            d.isEnvironmentFlag(),
            d.isApplicableGlobally()
        );
    }
}

11. Security (JWT – Industry Standard)

Stateless JWT

Filter-based authentication

No business logic in security layer

OncePerRequestFilter → JwtTokenValidator → SecurityContext

12. Exception Handling (Global)
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<ApiError> handleBadRequest(BadRequestException ex) {
        return ResponseEntity
            .badRequest()
            .body(new ApiError(400, ex.getMessage()));
    }
}

13. Configuration Best Practices
Config	Purpose
MongoConfig	Indexes, converters
SecurityConfig	JWT, filters
OpenApiConfig	Swagger
JacksonConfig	Enum/date handling
14. Production-Grade Practices

✔ Pagination ready
✔ Feature-flag friendly
✔ Log correlation IDs
✔ Metrics (Micrometer)
✔ Contract-first API
✔ Testable services

15. What This Knowledge Base Enables

AI agents generating code safely

Clean onboarding for new devs

Scalable microservice evolution

Zero controller business logic

MongoDB + Spring Boot alignment
