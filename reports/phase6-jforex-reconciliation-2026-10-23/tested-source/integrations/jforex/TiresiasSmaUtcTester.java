import com.dukascopy.api.*;
import java.io.BufferedWriter;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/** Historical tester only. No login, client connection, HTTP or live/demo orders. */
public class TiresiasSmaUtcTester implements IStrategy {
    @Configurable("Inicio UTC incluido (AAAA-MM-DD)") public String startDate = "2025-01-01";
    @Configurable("Fin UTC excluido (AAAA-MM-DD)") public String endDateExclusive = "2025-12-25";
    @Configurable("SMA rapida") public int fast = 20;
    @Configurable("SMA lenta") public int slow = 60;
    @Configurable("Cantidad EUR en unidades, minimo 1000") public long quantityEur = 1000;
    @Configurable("Capital inicial USD exigido al tester") public double expectedCapitalUsd = 1000000;
    @Configurable("Metodo de datos declarado (copiar del tester)") public String declaredFeed = "";

    private static final MathContext MC = new MathContext(28, RoundingMode.HALF_EVEN);
    private static final BigDecimal MILLION = new BigDecimal("1000000");
    private IContext context;
    private IEngine engine;
    private IDataService calendar;
    private Path directory;
    private BufferedWriter dailyFile, hourlyFile, eventsFile, calendarFile, accountFile, orderSnapshotsFile;
    private final List<Tracked> orders = new ArrayList<>();
    private final List<BigDecimal> closes = new ArrayList<>();
    private BigDecimal previousFast, previousSlow;
    private Day day;
    private long start, end, lastTick = -1, lastBar = -1, ticks;
    private long skippedOfflineTicks, offlineFirst, offlineLast, offlineCount;
    private long lastReceivedAt = -1;
    private double lastReceivedBid, lastReceivedAsk;
    private String problem = "";
    private boolean started, ended, stopped;
    private static class Configuration {
        final String first, limit, feed;
        final int fast, slow;
        final long quantity;
        final double capital;
        Configuration(String first, String limit, int fast, int slow, long quantity, double capital, String feed) {
            this.first=first;this.limit=limit;this.fast=fast;this.slow=slow;this.quantity=quantity;this.capital=capital;this.feed=feed;
        }
        String first() { return first; } String limit() { return limit; } String feed() { return feed; }
        int fast() { return fast; } int slow() { return slow; } long quantity() { return quantity; } double capital() { return capital; }
        boolean matches(Configuration other) {
            return first.equals(other.first) && limit.equals(other.limit) && feed.equals(other.feed)
                && fast==other.fast && slow==other.slow && quantity==other.quantity && capital==other.capital;
        }
    }
    private Configuration parameters;
    private Configuration snapshot() { return new Configuration(startDate, endDateExclusive, fast, slow, quantityEur, expectedCapitalUsd, declaredFeed); }
    private void unchangedParameters() {
        if (!parameters.matches(snapshot())) throw new IllegalArgumentException("Parametros cambiados: prepara otra prueba desde cero.");
    }

    private static class Tracked {
        IOrder order;
        final String label, entrySignal;
        String closeSignal = "";
        long requestedCloseAt = Long.MAX_VALUE;
        Tracked(String label, String signal) { this.label = label; this.entrySignal = signal; }
    }

    private static class Day {
        final LocalDate date;
        final long first;
        long last, count;
        final BigDecimal bidOpen, askOpen;
        BigDecimal bidHigh, bidLow, bidClose, askHigh, askLow, askClose;
        Day(long at, BigDecimal bid, BigDecimal ask) {
            date = Instant.ofEpochMilli(at).atZone(ZoneOffset.UTC).toLocalDate();
            first = at; bidOpen = bid; askOpen = ask;
            bidHigh = bidLow = bidClose = bid; askHigh = askLow = askClose = ask;
            add(at, bid, ask);
        }
        void add(long at, BigDecimal bid, BigDecimal ask) {
            last = at; count++;
            bidHigh = bidHigh.max(bid); bidLow = bidLow.min(bid); bidClose = bid;
            askHigh = askHigh.max(ask); askLow = askLow.min(ask); askClose = ask;
        }
    }

    private void testOnly() throws JFException {
        if (engine == null || engine.getType() != IEngine.Type.TEST)
            throw new JFException("Tiresias: solo Strategy Tester (TEST); DEMO y LIVE rechazados.");
    }

    @Override public void onStart(IContext supplied) throws JFException {
        if (engine != null) throw new JFException("Usa una instancia nueva para cada prueba.");
        context = supplied; engine = context.getEngine();
        testOnly(); // Before subscriptions, files, account queries or orders.
        try {
            LocalDate first = LocalDate.parse(startDate), limit = LocalDate.parse(endDateExclusive);
            start = first.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
            end = limit.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
            if (start >= end || limit.toEpochDay() - first.toEpochDay() > 730 || fast < 1 || fast >= slow || slow > 252)
                throw new IllegalArgumentException("Periodo o ventanas incompatibles.");
            if (quantityEur < 1000 || quantityEur > 100000 || !Double.isFinite(expectedCapitalUsd)
                    || expectedCapitalUsd <= 0 || expectedCapitalUsd > 1e9)
                throw new IllegalArgumentException("Cantidad o capital fuera de limites.");
            if (declaredFeed == null || !declaredFeed.matches("[A-Za-z0-9_.-]{1,100}"))
                throw new IllegalArgumentException("Declara el metodo del tester; ejemplo candles_h1_4ohlc_bid.");
            parameters = snapshot();
            IAccount account = context.getAccount();
            if (!"USD".equals(account.getAccountCurrency().getCurrencyCode())
                    || !Double.isFinite(account.getEquity()) || Math.abs(account.getEquity() - expectedCapitalUsd) > 0.000001
                    || account.getLeverage() != 1.0 || !engine.getOrders().isEmpty())
                throw new IllegalArgumentException("Tester nuevo requerido: USD, capital indicado, apalancamiento 1 y sin ordenes.");
            calendar = context.getDataService();
            if (calendar == null) throw new IllegalArgumentException("Calendario nativo del tester no disponible.");
            directory = Files.createDirectory(context.getFilesDir().toPath().resolve("tiresias-test-" + UUID.randomUUID()));
            dailyFile = writer("daily.csv"); hourlyFile = writer("hourly.csv"); eventsFile = writer("events.csv");
            calendarFile = writer("calendar.csv");
            accountFile = writer("account-snapshots.csv"); orderSnapshotsFile = writer("order-snapshots.csv");
            row(dailyFile, "date", "first_tick_at", "last_tick_at", "session_close_at", "bid_open", "bid_high", "bid_low", "bid_close",
                    "ask_open", "ask_high", "ask_low", "ask_close", "tick_count", "fast", "slow", "signal", "boundary_observed");
            row(hourlyFile, "open_at", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close", "bid_volume", "ask_volume");
            row(eventsFile, "type", "at", "label", "native_order_id", "signal_at", "quantity_eur", "bid", "ask", "native_content", "native_reasons");
            row(calendarFile, "first_skipped_tick_at", "last_skipped_tick_at", "skipped_ticks", "calendar_source");
            row(accountFile, "reason", "observed_at", "target_cutoff_at", "currency", "api_equity", "api_base_equity", "api_balance_eod",
                    "api_values_may_lag", "quote_at", "bid", "ask");
            row(orderSnapshotsFile, "reason", "observed_at", "target_cutoff_at", "native_order_id", "label", "state", "native_amount_millions",
                    "open_quantity_eur_from_history", "aggregate_commission_usd", "adjusted_open_price", "native_profit_loss_usd", "entry_parts", "close_parts");
            writeMetadata("started");
            context.setSubscribedInstruments(Collections.singleton(Instrument.EURUSD), true);
            started = true;
            context.getConsole().getOut().println("TIRESIAS TEST export: " + directory.toAbsolutePath());
        } catch (IOException | IllegalArgumentException | java.time.DateTimeException failure) {
            problem = failure.toString(); closeStreams(); throw new JFException(problem);
        }
    }

    @Override public void onTick(Instrument instrument, ITick tick) throws JFException {
        testOnly();
        if (!started || stopped || !problem.isEmpty() || !Instrument.EURUSD.equals(instrument)) return;
        try {
            unchangedParameters();
            long at = tick.getTime();
            lastReceivedAt = at; lastReceivedBid = tick.getBid(); lastReceivedAsk = tick.getAsk();
            if (at < start || ended) return;
            if (at < lastTick) throw new IllegalArgumentException("Ticks fuera de orden.");
            lastTick = at;
            if (at >= end) {
                captureSnapshot("strategy_cutoff");
                finishOfflineInterval();
                if (day != null) finishDay(true);
                ended = true; writeMetadata("strategy_window_end_observed"); return;
            }
            // Candle interpolation also emits flat weekend ticks. Ask the native
            // historical calendar before letting them create sessions or orders.
            if (calendar.isOfflineTime(at, instrument)) {
                if (offlineCount == 0) offlineFirst = at;
                offlineLast = at; offlineCount++; skippedOfflineTicks++;
                return;
            }
            finishOfflineInterval();
            BigDecimal bid = positive(tick.getBid()), ask = positive(tick.getAsk());
            if (ask.compareTo(bid) < 0) throw new IllegalArgumentException("Cotizaciones cruzadas.");
            LocalDate date = Instant.ofEpochMilli(at).atZone(ZoneOffset.UTC).toLocalDate();
            if (day != null && !date.equals(day.date)) {
                String signalAt = day.date.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant().toString();
                String signal = finishDay(true);
                request(signal, signalAt, at, bid, ask); // Only after the past day is complete.
            }
            if (day == null) day = new Day(at, bid, ask); else day.add(at, bid, ask);
            ticks++;
        } catch (IOException | RuntimeException | JFException failure) { fail(failure); }
    }

    private void finishOfflineInterval() throws IOException {
        if (offlineCount == 0) return;
        row(calendarFile, iso(offlineFirst), iso(offlineLast), offlineCount, "IDataService.isOfflineTime(time,EURUSD)");
        offlineCount = 0;
    }

    private BigDecimal openQuantityFromHistory(IOrder order) {
        List<IFillOrder> entries = order.getFillHistory(); List<ICloseOrder> exits = order.getCloseHistory();
        if (entries == null || exits == null) throw new IllegalArgumentException("Historial nativo ausente.");
        BigDecimal quantity = BigDecimal.ZERO;
        for (IFillOrder part : entries) quantity = quantity.add(positive(part.getAmount()).multiply(MILLION));
        for (ICloseOrder part : exits) quantity = quantity.subtract(positive(part.getAmount()).multiply(MILLION));
        if (quantity.signum() < 0) throw new IllegalArgumentException("Cierres superiores a entradas nativas.");
        return quantity;
    }

    private void captureSnapshot(String reason) throws IOException {
        if (lastReceivedAt < 0) return;
        IAccount account = context.getAccount();
        row(accountFile, reason, iso(lastReceivedAt), iso(end), account.getAccountCurrency().getCurrencyCode(),
                finite(account.getEquity()), finite(account.getBaseEquity()), finite(account.getBalance()), true,
                iso(lastReceivedAt), positive(lastReceivedBid), positive(lastReceivedAsk));
        for (Tracked item : orders) if (item.order != null) {
            IOrder order = item.order;
            row(orderSnapshotsFile, reason, iso(lastReceivedAt), iso(end), order.getId(), item.label, order.getState(),
                    nonnegative(order.getAmount()), openQuantityFromHistory(order), nonnegative(order.getCommissionInUSD()),
                    nonnegative(order.getOpenPrice()), finite(order.getProfitLossInUSD()), order.getFillHistory().size(), order.getCloseHistory().size());
        }
    }

    private String finishDay(boolean boundary) throws IOException {
        closes.add(day.bidClose);
        BigDecimal quick = average(parameters.fast()), gradual = average(parameters.slow());
        String signal = "none";
        if (boundary && previousFast != null && previousSlow != null && quick != null && gradual != null) {
            if (previousFast.compareTo(previousSlow) <= 0 && quick.compareTo(gradual) > 0) signal = "enter_long";
            else if (previousFast.compareTo(previousSlow) >= 0 && quick.compareTo(gradual) < 0) signal = "exit_long";
        }
        row(dailyFile, day.date, iso(day.first), iso(day.last), day.date.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant(),
                day.bidOpen, day.bidHigh, day.bidLow, day.bidClose, day.askOpen, day.askHigh, day.askLow, day.askClose,
                day.count, quick, gradual, boundary ? signal : "unconfirmed_last_session", boundary);
        previousFast = quick; previousSlow = gradual; day = null;
        return signal;
    }

    private BigDecimal average(int window) {
        if (closes.size() < window) return null;
        BigDecimal sum = BigDecimal.ZERO;
        for (int i = closes.size() - window; i < closes.size(); i++) sum = sum.add(closes.get(i), MC);
        return sum.divide(BigDecimal.valueOf(window), MC);
    }

    private void request(String signal, String signalAt, long at, BigDecimal bid, BigDecimal ask) throws JFException, IOException {
        testOnly();
        for (IOrder active : engine.getOrders()) {
            if (orders.stream().noneMatch(item -> item.label.equals(active.getLabel())))
                throw new IllegalArgumentException("Otra estrategia tiene una orden activa en este tester.");
        }
        Tracked open = null;
        for (Tracked item : orders) {
            if (item.order == null || item.order.getState() == IOrder.State.CREATED || item.order.getState() == IOrder.State.OPENED)
                throw new IllegalArgumentException("Orden anterior aun pendiente al cambiar de sesion.");
            if (item.order.getState() == IOrder.State.FILLED) {
                if (!item.closeSignal.isEmpty()) throw new IllegalArgumentException("Cierre anterior sin confirmar.");
                if (open != null) throw new IllegalArgumentException("Mas de una posicion abierta.");
                open = item;
            }
        }
        if ("enter_long".equals(signal) && open == null) {
            if (orders.size() >= 1000) throw new IllegalArgumentException("Limite de ordenes de investigacion.");
            Tracked item = new Tracked("Tiresias_" + UUID.randomUUID().toString().replace("-", ""), signalAt);
            orders.add(item); // Registered before a possibly synchronous tester callback.
            row(eventsFile, "buy_request_not_fill", iso(at), item.label, "", signalAt, parameters.quantity(), bid, ask, "", "");
            testOnly();
            item.order = engine.submitOrder(item.label, Instrument.EURUSD, IEngine.OrderCommand.BUY,
                    BigDecimal.valueOf(parameters.quantity()).divide(MILLION).doubleValue());
        } else if ("exit_long".equals(signal) && open != null) {
            open.closeSignal = signalAt;
            open.requestedCloseAt = at;
            row(eventsFile, "close_request_not_fill", iso(at), open.label, open.order.getId(), signalAt,
                    positive(open.order.getAmount()).multiply(MILLION), bid, ask, "", "");
            testOnly(); open.order.close();
        }
    }

    @Override public void onBar(Instrument instrument, Period period, IBar ask, IBar bid) throws JFException {
        testOnly();
        if (!started || stopped || !problem.isEmpty() || !Instrument.EURUSD.equals(instrument) || !Period.ONE_HOUR.equals(period)) return;
        try {
            unchangedParameters();
            long at = bid.getTime();
            if (at < start || at >= end) return;
            if (at != ask.getTime() || at <= lastBar) throw new IllegalArgumentException("Barras H1 desalineadas o fuera de orden.");
            row(hourlyFile, iso(at), positive(bid.getOpen()), positive(bid.getHigh()), positive(bid.getLow()), positive(bid.getClose()),
                    positive(ask.getOpen()), positive(ask.getHigh()), positive(ask.getLow()), positive(ask.getClose()), nonnegative(bid.getVolume()), nonnegative(ask.getVolume()));
            lastBar = at;
        } catch (IOException | IllegalArgumentException failure) { fail(failure); }
    }

    @Override public void onMessage(IMessage message) throws JFException {
        testOnly();
        if (!started || stopped || message.getOrder() == null) return;
        IOrder order = message.getOrder();
        for (Tracked item : orders) if (item.label.equals(order.getLabel())) {
            item.order = order;
            try {
                row(eventsFile, message.getType(), iso(message.getCreationTime()), item.label, order.getId(), "", "", "", "",
                        message.getContent(), message.getReasons());
                if (message.getType() == IMessage.Type.ORDER_CLOSE_REJECTED) { item.closeSignal = ""; item.requestedCloseAt = Long.MAX_VALUE; }
                if (message.getType().name().contains("REJECTED")) fail(new IllegalArgumentException("Rechazo nativo: " + message.getType() + "; " + message.getContent()));
            } catch (IOException failure) { fail(failure); }
            return;
        }
    }

    @Override public void onAccount(IAccount account) throws JFException { testOnly(); }

    @Override public void onStop() throws JFException {
        try {
            testOnly();
            if (!started || stopped) return;
            stopped = true;
            if (!parameters.matches(snapshot())) problem = "Parametros cambiados durante la prueba.";
            if (problem.isEmpty()) captureSnapshot("tester_stop");
            finishOfflineInterval();
            if (day != null) finishDay(false); // No claim that an interrupted final day is complete.
            try (BufferedWriter fills = writer("executions.csv"); BufferedWriter totals = writer("orders.csv")) {
                row(fills, "external_id", "executed_at", "side", "quantity", "price", "fee", "signal_at", "native_order_id", "history_index", "in_strategy_window", "signal_binding");
                row(totals, "native_order_id", "label", "state", "native_amount_millions", "aggregate_commission_usd", "entry_parts", "close_parts", "open_quantity_eur_from_history");
                for (Tracked item : orders) if (item.order != null) {
                    IOrder order = item.order;
                    List<IFillOrder> entries = order.getFillHistory(); List<ICloseOrder> exits = order.getCloseHistory();
                    if (entries == null || exits == null) throw new IllegalArgumentException("Historial nativo ausente.");
                    if ((order.getState() == IOrder.State.FILLED || order.getState() == IOrder.State.CLOSED) && entries.isEmpty()
                            || order.getState() == IOrder.State.CLOSED && exits.isEmpty())
                        throw new IllegalArgumentException("Estado nativo sin historial de ejecuciones suficiente.");
                    int index = 0;
                    for (IFillOrder part : entries) exportPart(fills, order, part, "buy", item.entrySignal, ++index);
                    index = 0;
                    for (ICloseOrder part : exits) exportPart(fills, order, part, "sell",
                            problem.isEmpty() && part.getTime() >= item.requestedCloseAt ? item.closeSignal : "", ++index);
                    row(totals, order.getId(), item.label, order.getState(), order.getAmount(), nonnegative(order.getCommissionInUSD()), entries.size(), exits.size(), openQuantityFromHistory(order));
                }
            }
            writeMetadata(problem.isEmpty() ? "stopped_review_native_report" : "failed_review_partial_exports");
        } catch (IOException | IllegalArgumentException failure) {
            problem = failure.toString();
            try { writeMetadata("failed_review_partial_exports"); } catch (IOException ignored) { /* Preserve failure. */ }
            throw new JFException(problem);
        } finally { closeStreams(); }
    }

    private void exportPart(BufferedWriter file, IOrder order, IPartialOrder part, String side, String signal, int index) throws IOException {
        long at = part.getTime();
        row(file, "", iso(at), side, positive(part.getAmount()).multiply(MILLION), positive(part.getPrice()), "", signal,
                order.getId(), side + "-" + index, at >= start && at < end,
                signal.isEmpty() ? "unknown" : "strategy_request_unverified_native_causality");
    }

    private void fail(Exception failure) throws JFException {
        problem = failure.toString();
        try { writeMetadata("failed_review_partial_exports"); } catch (IOException secondary) { problem += "; " + secondary; }
        context.getConsole().getErr().println("TIRESIAS detenido: " + problem);
        context.stop(); // Stop the strategy; never close positions in onStop.
        throw new JFException(problem);
    }

    private BufferedWriter writer(String name) throws IOException {
        return Files.newBufferedWriter(directory.resolve(name), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    private static String iso(long at) { return Instant.ofEpochMilli(at).toString(); }
    private static BigDecimal positive(double value) {
        BigDecimal result = nonnegative(value);
        if (result.signum() == 0) throw new IllegalArgumentException("Precio o cantidad cero.");
        return result;
    }
    private static BigDecimal nonnegative(double value) {
        if (!Double.isFinite(value) || value < 0) throw new IllegalArgumentException("Numero nativo incompatible.");
        return BigDecimal.valueOf(value);
    }
    private static BigDecimal finite(double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Numero nativo no finito.");
        return BigDecimal.valueOf(value);
    }
    private static void row(BufferedWriter file, Object... values) throws IOException {
        for (int i = 0; i < values.length; i++) {
            if (i > 0) file.write(',');
            Object value = values[i];
            String text = value == null ? "" : value instanceof BigDecimal ? ((BigDecimal)value).stripTrailingZeros().toPlainString() : value.toString();
            file.write('"'); file.write(text.replace("\"", "\"\"")); file.write('"');
        }
        file.write('\n'); file.flush();
    }
    private void writeMetadata(String status) throws IOException {
        if (directory == null) return;
        if (!problem.isEmpty()) Files.write(directory.resolve("failure.txt"), problem.getBytes(StandardCharsets.UTF_8));
        String value = "{\n  \"protocol\":\"tiresias_jforex_test_export_v3\",\n  \"strategy_revision\":\"sma_utc_test_v3_cutoff_snapshots\",\n  \"engine_type\":\"TEST\",\n"
            + "  \"status\":\"" + status + "\",\n  \"pair\":\"EUR/USD\",\n  \"currency\":\"USD\",\n  \"strategy\":\"sma\",\n"
            + "  \"fast\":" + parameters.fast() + ",\n  \"slow\":" + parameters.slow() + ",\n  \"quantity_eur\":\"" + parameters.quantity() + "\",\n"
            + "  \"expected_initial_capital_usd\":\"" + BigDecimal.valueOf(parameters.capital()).toPlainString() + "\",\n"
            + "  \"start_date\":\"" + parameters.first() + "\",\n  \"end_date_exclusive\":\"" + parameters.limit() + "\",\n"
            + "  \"declared_feed\":\"" + parameters.feed() + "\",\n  \"feed_configuration_verified\":false,\n"
            + "  \"session_basis\":\"observed_utc_tester_ticks_excluding_native_offline\",\n  \"execution_request\":\"first_online_tick_of_next_observed_utc_session\",\n"
            + "  \"offline_calendar_source\":\"IDataService.isOfflineTime(time,EURUSD)\",\n  \"offline_ticks_skipped\":" + skippedOfflineTicks + ",\n"
            + "  \"strategy_window_end_observed\":" + ended + ",\n  \"ticks_processed\":" + ticks + ",\n"
            + "  \"strategy_forced_final_liquidation\":false,\n  \"native_final_report_reconciled\":false,\n"
            + "  \"per_execution_fee_available\":false,\n  \"aggregate_fees_allocated_to_fills\":false,\n"
            + "  \"account_snapshots_api_values_may_lag\":true,\n  \"api_balance_is_previous_eod_not_cash\":true,\n"
            + "  \"external_equivalence_verified\":false,\n  \"has_failure\":" + !problem.isEmpty() + "\n}\n";
        Files.write(directory.resolve("metadata.json"), value.getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }
    private void closeStreams() {
        for (BufferedWriter file : new BufferedWriter[]{dailyFile, hourlyFile, eventsFile, calendarFile, accountFile, orderSnapshotsFile}) if (file != null) {
            try { file.close(); } catch (IOException ignored) { /* Preserve the original failure. */ }
        }
    }
}
