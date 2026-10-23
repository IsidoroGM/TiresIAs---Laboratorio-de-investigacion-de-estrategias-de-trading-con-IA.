import com.dukascopy.api.*;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Offline API-interface doubles. Never starts a JForex client or native tester. */
public class JForexHarness {
    interface Calls { Object call(Method method, Object[] args) throws Throwable; }
    @SuppressWarnings("unchecked") static <T> T fake(Class<T> type, Calls calls) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, (p, method, args) -> {
            if (method.getDeclaringClass() == Object.class) {
                if (method.getName().equals("equals")) return p == args[0];
                if (method.getName().equals("hashCode")) return System.identityHashCode(p);
                return "offline_" + type.getSimpleName();
            }
            return calls.call(method, args);
        });
    }
    static class Host {
        String scenario;
        Path root;
        final TiresiasSmaUtcTester strategy = new TiresiasSmaUtcTester();
        IEngine.Type mode = IEngine.Type.TEST;
        final List<Book> book = new ArrayList<>();
        final List<long[]> offlineRanges = new ArrayList<>();
        int submissions, closures, subscriptions, fileQueries, stops, calendarQueries;
        long at;
        double bid, ask;
        boolean foreign;
        final PrintStream sink = new PrintStream(new ByteArrayOutputStream(), true, StandardCharsets.UTF_8);
        final IConsole console = fake(IConsole.class, (m,a) -> {
            if (m.getName().equals("getOut") || m.getName().equals("getErr") || m.getName().equals("getWarn")) return sink;
            throw new AssertionError(m);
        });
        final ICurrency currency = fake(ICurrency.class, (m,a) -> {
            if (m.getName().equals("getCurrencyCode")) return scenario.equals("invalid_currency") ? "EUR" : "USD";
            throw new AssertionError(m);
        });
        final IAccount account = fake(IAccount.class, (m,a) -> {
            switch(m.getName()) {
                case "getAccountCurrency": return currency;
                case "getEquity": return scenario.equals("invalid_capital") ? 1000.0 : 1000000.0;
                case "getLeverage": return scenario.equals("invalid_leverage") ? 100.0 : 1.0;
                default: throw new AssertionError("Forbidden account call " + m);
            }
        });
        final IDataService calendar = fake(IDataService.class, (m,a) -> {
            if (!m.getName().equals("isOfflineTime") || a.length != 2 || a[1] != Instrument.EURUSD)
                throw new AssertionError("Expected the historical instrument-specific calendar: " + m);
            calendarQueries++;
            if (scenario.equals("calendar_failure")) throw new IllegalStateException("fixture_calendar_unavailable");
            long time = (Long)a[0];
            return offlineRanges.stream().anyMatch(range -> time >= range[0] && time < range[1]);
        });
        final IEngine engine = fake(IEngine.class, (m,a) -> {
            switch(m.getName()) {
                case "getType": return mode;
                case "getOrders":
                    List<IOrder> active = new ArrayList<>();
                    for (Book b:book) if (b.state != IOrder.State.CLOSED && b.state != IOrder.State.CANCELED) active.add(b.order);
                    if (foreign || scenario.equals("invalid_existing_orders")) active.add(fake(IOrder.class, (m2,a2) -> {
                        if (m2.getName().equals("getLabel")) return "unrelated_strategy";
                        throw new AssertionError(m2);
                    }));
                    return active;
                case "submitOrder":
                    if (mode != IEngine.Type.TEST) throw new AssertionError("Non-test order");
                    submissions++;
                    if (scenario.equals("rejected")) throw new JFException("fixture_submit_rejected");
                    if (a[1] != Instrument.EURUSD || a[2] != IEngine.OrderCommand.BUY || ((Double)a[3]) != 0.001)
                        throw new AssertionError("Wrong instrument, direction or million-unit conversion");
                    Book b=new Book(this,(String)a[0],(Double)a[3]);book.add(b);
                    if (scenario.equals("native_rejection_message")) {
                        strategy.onMessage(message(b.order,IMessage.Type.ORDER_SUBMIT_REJECTED));
                        throw new AssertionError("Native rejection was silently ignored");
                    }
                    strategy.onMessage(message(b.order,IMessage.Type.ORDER_SUBMIT_OK));
                    if (!scenario.equals("pending")) strategy.onMessage(message(b.order,IMessage.Type.ORDER_FILL_OK));
                    return b.order;
                default: throw new AssertionError("Forbidden engine call " + m);
            }
        });
        final IContext context = fake(IContext.class, (m,a) -> {
            switch(m.getName()) {
                case "getEngine": return engine;
                case "getAccount": return account;
                case "getConsole": return console;
                case "getDataService": calendarQueries++;return scenario.equals("calendar_missing") ? null : calendar;
                case "getFilesDir": fileQueries++;return root.toFile();
                case "setSubscribedInstruments": subscriptions++;return null;
                case "stop": stops++;return null;
                default: throw new AssertionError("Forbidden context call " + m);
            }
        });
        Host(String scenario,Path root) {
            this.scenario=scenario;this.root=root;
            strategy.fast=2;strategy.slow=3;strategy.endDateExclusive="2025-01-09";
            strategy.declaredFeed="offline_fixture_not_jforex_tester";
        }
        IMessage message(IOrder order,IMessage.Type type) {
            return fake(IMessage.class,(m,a)-> {
                switch(m.getName()) {
                    case "getOrder":return order;
                    case "getType":return type;
                    case "getCreationTime":return at;
                    case "getContent":return type == IMessage.Type.ORDER_SUBMIT_REJECTED ? "System offline" : "fixture confirmation";
                    case "getReasons":return Collections.emptySet();
                    default:throw new AssertionError(m);
                }
            });
        }
        void tick(long time,double value,double offer) throws Exception {
            at=time;bid=value;ask=offer;
            strategy.onTick(Instrument.EURUSD,fake(ITick.class,(m,a)-> {
                switch(m.getName()) {
                    case "getTime":return at;
                    case "getBid":return bid;
                    case "getAsk":return ask;
                    default:throw new AssertionError(m);
                }
            }));
        }
        IBar bar(long time,double value,double volume) {
            return fake(IBar.class,(m,a)-> {
                switch(m.getName()) {
                    case "getTime":return time;
                    case "getOpen":case "getClose":case "getHigh":case "getLow":return value;
                    case "getVolume":return volume;
                    default:throw new AssertionError(m);
                }
            });
        }
        void days() throws Exception {
            long start=Instant.parse("2025-01-01T00:00:00Z").toEpochMilli();
            double[] prices={1,1,1,2,1,0.8,1.5,2};
            for(int i=0;i<prices.length;i++) {
                tick(start+i*86400000L,prices[i],prices[i]+0.0002);
                tick(start+i*86400000L+86399999,prices[i],prices[i]+0.0002);
            }
            if (!scenario.equals("unfinished")) tick(start+8*86400000L,2,2.0002);
        }
        void offlineGap(boolean endOnSaturday) throws Exception {
            long monday=Instant.parse("2025-01-06T00:00:00Z").toEpochMilli();
            long close=Instant.parse("2025-01-10T22:00:00Z").toEpochMilli();
            long reopen=Instant.parse("2025-01-12T22:00:00Z").toEpochMilli();
            offlineRanges.add(new long[]{close,reopen});
            for (int i=0;i<5;i++) {
                double price=i==4 ? 2 : 1;
                tick(monday+i*86400000L,price,price+0.0002);
                tick(monday+i*86400000L+20*3600000,price,price+0.0002);
            }
            tick(close+3600000,99,99.0002);
            if (endOnSaturday) {
                tick(Instant.parse("2025-01-11T00:00:00Z").toEpochMilli(),99,99.0002);
                return;
            }
            tick(Instant.parse("2025-01-11T12:00:00Z").toEpochMilli(),1234,1234.0002);
            tick(Instant.parse("2025-01-12T00:00:00Z").toEpochMilli(),9999,9999.0002);
            tick(reopen-1,1111,1111.0002);
            tick(reopen,2.5,2.5002);
            tick(reopen+3600000,2.5,2.5002);
            tick(Instant.parse("2025-01-13T00:00:00Z").toEpochMilli(),2.5,2.5002);
        }
    }
    static class Book {
        final Host host;
        final String label;
        final String id;
        IOrder.State state;
        double amount, commission;
        final List<IFillOrder> entries=new ArrayList<>();
        final List<ICloseOrder> exits=new ArrayList<>();
        IOrder order;
        Book(Host host,String label,double amount) {
            this.host=host;this.label=label;this.id="offline-order-"+host.submissions;this.amount=amount;
            state=host.scenario.equals("native_rejection_message") ? IOrder.State.CANCELED : host.scenario.equals("pending")?IOrder.State.OPENED:IOrder.State.FILLED;
            if (!host.scenario.equals("pending") && !host.scenario.equals("native_rejection_message")) {
                if(host.scenario.equals("partial")) {
                    entries.add(part(IFillOrder.class,host.at,host.ask,0.0004));
                    entries.add(part(IFillOrder.class,host.at,host.ask+0.0001,0.0006));
                } else entries.add(part(IFillOrder.class,host.at,host.ask,amount));
                commission=1.234;
                if(host.scenario.equals("earlier_native_close")) {
                    exits.add(part(ICloseOrder.class,host.at+3600000,host.bid,0.0004));this.amount=0.0006;
                }
            }
            order=fake(IOrder.class,(m,a)-> {
                switch(m.getName()) {
                    case "getId":return id;
                    case "getLabel":return label;
                    case "getState":return state;
                    case "getAmount":return this.amount;
                    case "getCommissionInUSD":return commission;
                    case "getFillHistory":return host.scenario.equals("history_missing")?new ArrayList<IFillOrder>():entries;
                    case "getCloseHistory":return exits;
                    case "close":
                        if(host.mode!=IEngine.Type.TEST)throw new AssertionError("Non-test close");
                        host.closures++;state=IOrder.State.CLOSED;
                        if(host.scenario.equals("partial")) {
                            exits.add(part(ICloseOrder.class,host.at,host.bid,0.0003));
                            exits.add(part(ICloseOrder.class,host.at,host.bid-0.0001,0.0007));
                        } else exits.add(part(ICloseOrder.class,host.at,host.bid,this.amount));
                        this.amount=0;commission+=2.345;
                        host.strategy.onMessage(host.message(this.order,IMessage.Type.ORDER_CLOSE_OK));return null;
                    default:throw new AssertionError("Forbidden order call "+m);
                }
            });
        }
    }
    static <T> T part(Class<T> type,long at,double price,double amount) {
        return fake(type,(m,a)-> {
            switch(m.getName()) {
                case "getTime":return at;
                case "getPrice":return price;
                case "getAmount":return amount;
                default:throw new AssertionError(m);
            }
        });
    }
    public static void main(String[] args) throws Exception {
        if(args[0].equals("batch")) {
            String[] scenarios={"cross","partial","unfinished","stop_twice","guard_live","guard_demo","guard_callbacks",
                "invalid_quantity","invalid_quantity_max","invalid_windows","invalid_date","invalid_feed","invalid_nan",
                "invalid_currency","invalid_capital","invalid_leverage","invalid_existing_orders","out_of_order","crossed",
                "bad_price","hourly","hourly_duplicate","hourly_nan","foreign","pending","rejected","history_missing","mutated_parameters","earlier_native_close",
                "calendar_missing","calendar_failure","offline_gap","offline_final_boundary","native_rejection_message"};
            for(String name:scenarios)main(new String[]{name,Path.of(args[1]).resolve(name).toString()});
            return;
        }
        String scenario=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);
        Host host=new Host(scenario,root);boolean rejected=false;
        if(scenario.equals("guard_live"))host.mode=IEngine.Type.LIVE;
        if(scenario.equals("guard_demo"))host.mode=IEngine.Type.DEMO;
        if(scenario.equals("invalid_quantity"))host.strategy.quantityEur=1;
        if(scenario.equals("invalid_quantity_max"))host.strategy.quantityEur=100001;
        if(scenario.equals("invalid_windows"))host.strategy.fast=3;
        if(scenario.equals("invalid_date"))host.strategy.startDate="not-a-date";
        if(scenario.equals("invalid_feed"))host.strategy.declaredFeed="";
        if(scenario.equals("invalid_nan"))host.strategy.expectedCapitalUsd=Double.NaN;
        if(scenario.equals("offline_gap") || scenario.equals("offline_final_boundary")) {
            host.strategy.startDate="2025-01-06";
            host.strategy.endDateExclusive=scenario.equals("offline_gap") ? "2025-01-13" : "2025-01-11";
        }
        if(scenario.equals("replay")) {
            host.strategy.fast=Integer.parseInt(args[3]);host.strategy.slow=Integer.parseInt(args[4]);
            host.strategy.startDate=args[5];host.strategy.endDateExclusive=args[6];
        }
        try {
            host.strategy.onStart(host.context);
            switch(scenario) {
                case "offline_gap":host.offlineGap(false);break;
                case "offline_final_boundary":host.offlineGap(true);break;
                case "mutated_parameters":host.strategy.quantityEur=2000;host.days();break;
                case "guard_callbacks":
                    host.mode=IEngine.Type.LIVE;
                    int blocks=0;
                    try {host.tick(Instant.parse("2025-01-01T00:00:00Z").toEpochMilli(),1,1.0002);}catch(JFException e){blocks++;}
                    try {host.strategy.onMessage(host.message(null,IMessage.Type.ORDER_FILL_OK));}catch(JFException e){blocks++;}
                    try {host.strategy.onAccount(host.account);}catch(JFException e){blocks++;}
                    try {host.strategy.onBar(Instrument.EURUSD,Period.ONE_HOUR,host.bar(0,1,1),host.bar(0,1,1));}catch(JFException e){blocks++;}
                    try {host.strategy.onStop();}catch(JFException e){blocks++;}
                    if(blocks!=5)throw new AssertionError("Callback guard bypass");
                    break;
                case "out_of_order":case "crossed":case "bad_price":
                    long at=Instant.parse("2025-01-01T00:00:01Z").toEpochMilli();host.tick(at,1,1.0002);
                    host.tick(scenario.equals("out_of_order")?at-1:at+1,scenario.equals("bad_price")?Double.NaN:1,scenario.equals("crossed")?0.99:1.0002);break;
                case "hourly":case "hourly_duplicate":case "hourly_nan":
                    long t=Instant.parse("2025-01-01T00:00:00Z").toEpochMilli();
                    host.strategy.onBar(Instrument.EURUSD,Period.ONE_HOUR,host.bar(t,1.0002,1),host.bar(t,1,scenario.equals("hourly_nan")?Double.NaN:1));
                    if(scenario.equals("hourly_duplicate"))host.strategy.onBar(Instrument.EURUSD,Period.ONE_HOUR,host.bar(t,1.0002,1),host.bar(t,1,1));break;
                case "foreign":host.foreign=true;host.days();break;
                case "replay":
                    List<String> lines=Files.readAllLines(Path.of(args[2]),StandardCharsets.UTF_8);
                    for(String line:lines.subList(1,lines.size())) {
                        String[] parts=line.split(",");host.tick(Long.parseLong(parts[0]),Double.parseDouble(parts[1]),Double.parseDouble(parts[2]));
                    }break;
                default:host.days();
            }
        }catch(JFException expected){rejected=true;}
        if(!scenario.equals("guard_callbacks")) {
            try {host.strategy.onStop();}catch(JFException expected){rejected=true;}
            if(scenario.equals("stop_twice"))host.strategy.onStop();
        }
        System.out.println("{\"scenario\":\""+scenario+"\",\"offline_api_doubles_only\":true,\"native_tester_run\":false,\"rejected\":"+rejected+
            ",\"submissions\":"+host.submissions+",\"closures\":"+host.closures+",\"subscriptions\":"+host.subscriptions+
            ",\"file_queries\":"+host.fileQueries+",\"stop_requests\":"+host.stops+",\"calendar_queries\":"+host.calendarQueries+"}");
    }
}
