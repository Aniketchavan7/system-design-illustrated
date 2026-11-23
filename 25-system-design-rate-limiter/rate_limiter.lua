-- Production Redis Token Bucket Rate Limiter
-- Executed atomically via EVALSHA
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- 1. Fetch current tokens and last refill timestamp
local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if not tokens then
    tokens = capacity
    last_refill = now
else
    -- 2. Lazy arithmetic token refill
    local elapsed = math.max(0, now - last_refill)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_refill = now
end

-- 3. Check and deduct tokens
if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
    return {1, math.floor(tokens), 0} -- Allowed, remaining, retry_after
else
    local needed = requested - tokens
    local retry_after = math.ceil(needed / refill_rate)
    return {0, math.floor(tokens), retry_after} -- Denied, remaining, retry_after
end
